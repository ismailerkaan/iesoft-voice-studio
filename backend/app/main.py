"""IESOFT Voice Studio API. Run: .venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8765"""
import logging
import threading
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import audio, config
from .jobs import BusyError, EngineNotReadyError, JobManager
from .schemas import GenerateRequest, GenerationSettings, ProfileIn, SplitRequest
from .storage import DuplicateNameError, Storage, is_valid_id, new_id
from .text_splitter import prepare_chunks

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

_ALLOWED_HOSTS = ["127.0.0.1", "localhost"]
_ALLOWED_ORIGIN_HOSTS = {"127.0.0.1", "localhost"}
_TZ = ZoneInfo("Europe/Istanbul")


def _require_id(value: str) -> str:
    if not is_valid_id(value):
        raise HTTPException(404, "Kayıt bulunamadı.")
    return value


def create_app(engine=None, storage: Storage | None = None, autoload: bool = True) -> FastAPI:
    if engine is None:
        from .tts_engine import ChatterboxEngine

        engine = ChatterboxEngine()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        config.ensure_dirs()
        app.state.storage = storage or Storage(config.DB_PATH)
        app.state.jobs = JobManager(engine, app.state.storage)
        if autoload:
            threading.Thread(target=engine.load, daemon=True, name="model-load").start()
        yield
        app.state.storage.close()

    app = FastAPI(title="IESOFT Voice Studio", lifespan=lifespan)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_ALLOWED_HOSTS + ["testserver"])

    @app.middleware("http")
    async def block_cross_origin_writes(request: Request, call_next):
        # Blocks other websites from driving the local API (CSRF) via form posts.
        origin = request.headers.get("origin")
        if request.method not in ("GET", "HEAD", "OPTIONS") and origin:
            host = origin.split("://", 1)[-1].split(":", 1)[0]
            if host not in _ALLOWED_ORIGIN_HOSTS:
                return JSONResponse({"detail": "Bu istek kaynağına izin verilmiyor."}, status_code=403)
        return await call_next(request)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        messages = []
        for err in exc.errors():
            field = ".".join(str(p) for p in err.get("loc", [])[1:])
            msg = err.get("msg", "Geçersiz değer").removeprefix("Value error, ")
            messages.append(f"{field}: {msg}" if field and field != "text" else msg)
        return JSONResponse({"detail": " • ".join(messages) or "Geçersiz istek."}, status_code=422)

    def store(request: Request) -> Storage:
        return request.app.state.storage

    def jobs(request: Request) -> JobManager:
        return request.app.state.jobs

    def reference_or_404(request: Request, ref_id: str | None) -> Path | None:
        if not ref_id:
            return None
        if not is_valid_id(ref_id) or not store(request).get_reference(ref_id):
            raise HTTPException(404, "Seçilen referans ses bulunamadı.")
        path = config.REFERENCES_DIR / f"{ref_id}.wav"
        if not path.exists():
            raise HTTPException(404, "Referans ses dosyası diskte bulunamadı.")
        return path

    # --- status & text
    @app.get("/api/status")
    def status(request: Request):
        job = jobs(request).current
        return {
            "model": {"status": engine.status, "device": engine.device, "error": engine.error, "name": "Chatterbox Multilingual V3"},
            "busy": bool(job and job.status == "running"),
            "max_text_chars": config.MAX_TEXT_CHARS,
            "default_settings": GenerationSettings().model_dump(),
        }

    @app.post("/api/text/split")
    def split(body: SplitRequest):
        # Shows exactly what the model will read (after Turkish normalisation).
        return {"chunks": [c.text for c in prepare_chunks(body.text)]}

    # --- reference voices
    @app.get("/api/references")
    def list_references(request: Request):
        return store(request).list_references()

    @app.post("/api/references", status_code=201)
    async def upload_reference(request: Request, file: UploadFile = File(...), consent: bool = Form(False)):
        if not consent:
            raise HTTPException(400, "Referans sesi kullanma izniniz olduğunu onaylamalısınız.")
        data = await file.read(config.MAX_REFERENCE_BYTES + 1)
        ref_id = new_id()
        dest = config.REFERENCES_DIR / f"{ref_id}.wav"
        try:
            duration = audio.sanitize_reference(data, dest)
        except audio.AudioError as exc:
            dest.unlink(missing_ok=True)
            raise HTTPException(400, str(exc)) from exc
        return store(request).add_reference(ref_id, file.filename or "referans.wav", duration)

    @app.get("/api/references/{ref_id}/audio")
    def reference_audio(request: Request, ref_id: str):
        return FileResponse(reference_or_404(request, ref_id), media_type="audio/wav")

    # --- profiles
    @app.get("/api/profiles")
    def list_profiles(request: Request):
        return store(request).list_profiles()

    def save_profile(request: Request, profile_id: str | None, body: ProfileIn):
        reference_or_404(request, body.reference_id)
        try:
            return store(request).save_profile(profile_id, body.name, body.reference_id, body.settings.model_dump())
        except DuplicateNameError:
            raise HTTPException(409, f"“{body.name}” adında bir profil zaten var.")

    @app.post("/api/profiles", status_code=201)
    def create_profile(request: Request, body: ProfileIn):
        return save_profile(request, None, body)

    @app.put("/api/profiles/{profile_id}")
    def update_profile(request: Request, profile_id: str, body: ProfileIn):
        if not store(request).get_profile(_require_id(profile_id)):
            raise HTTPException(404, "Profil bulunamadı.")
        return save_profile(request, profile_id, body)

    @app.delete("/api/profiles/{profile_id}", status_code=204)
    def delete_profile(request: Request, profile_id: str):
        if not store(request).delete_profile(_require_id(profile_id)):
            raise HTTPException(404, "Profil bulunamadı.")

    # --- generation jobs
    @app.post("/api/generate", status_code=202)
    def generate(request: Request, body: GenerateRequest):
        ref_path = reference_or_404(request, body.reference_id)
        profile_name = None
        if body.profile_id:
            profile = store(request).get_profile(_require_id(body.profile_id))
            profile_name = profile["name"] if profile else None
        try:
            return jobs(request).start(body, ref_path, profile_name).to_dict()
        except EngineNotReadyError:
            msg = "Model henüz hazır değil." if engine.status != "error" else f"Model yüklenemedi: {engine.error}"
            raise HTTPException(503, msg)
        except BusyError:
            raise HTTPException(409, "Şu anda başka bir seslendirme sürüyor. Bitmesini bekleyin.")

    @app.get("/api/jobs/current")
    def current_job(request: Request):
        job = jobs(request).current
        return job.to_dict() if job else None

    @app.get("/api/jobs/{job_id}")
    def get_job(request: Request, job_id: str):
        job = jobs(request).get(job_id)
        if not job:
            raise HTTPException(404, "İş bulunamadı.")
        return job.to_dict()

    @app.post("/api/jobs/{job_id}/cancel")
    def cancel_job(request: Request, job_id: str):
        if not jobs(request).cancel(job_id):
            raise HTTPException(409, "İptal edilecek çalışan bir iş yok.")
        return jobs(request).get(job_id).to_dict()

    # --- history & downloads
    @app.get("/api/generations")
    def list_generations(request: Request):
        return store(request).list_generations()

    @app.get("/api/generations/{gen_id}/audio")
    def generation_audio(
        request: Request,
        gen_id: str,
        format: str = Query("wav", pattern="^(wav|mp3)$"),
        download: bool = False,
    ):
        gen = store(request).get_generation(_require_id(gen_id))
        wav_path = config.GENERATIONS_DIR / f"{gen_id}.wav"
        if not gen or not wav_path.exists():
            raise HTTPException(404, "Ses dosyası bulunamadı.")
        path, media = wav_path, "audio/wav"
        if format == "mp3":
            path, media = wav_path.with_suffix(".mp3"), "audio/mpeg"
            if not path.exists():
                try:
                    audio.wav_to_mp3(wav_path, path)
                except Exception as exc:
                    raise HTTPException(500, str(exc)) from exc
        stamp = datetime.fromisoformat(gen["created_at"]).astimezone(_TZ).strftime("%Y%m%d_%H%M")
        filename = f"iesoft_{stamp}_{gen_id[:6]}.{format}" if download else None
        return FileResponse(path, media_type=media, filename=filename)

    # --- frontend (built React app)
    if config.FRONTEND_DIST.exists():
        app.mount("/", StaticFiles(directory=config.FRONTEND_DIST, html=True), name="frontend")

    return app


app = create_app()
