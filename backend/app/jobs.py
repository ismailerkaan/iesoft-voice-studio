"""Single-slot generation worker. Only one synthesis runs at a time."""
import logging
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path

from . import audio, config
from .schemas import GenerateRequest
from .storage import Storage, new_id
from .text_splitter import prepare_chunks

log = logging.getLogger("iesoft.jobs")


class BusyError(RuntimeError):
    pass


class EngineNotReadyError(RuntimeError):
    pass


@dataclass
class Job:
    id: str
    status: str = "running"  # running | done | error | cancelled
    stage: str = "Hazırlanıyor"
    chunk_index: int = 0
    chunk_total: int = 0
    current_text: str = ""
    error: str | None = None
    generation: dict | None = None
    started_at: float = field(default_factory=time.time)
    finished_at: float | None = None
    cancel_requested: bool = False

    def to_dict(self) -> dict:
        end = self.finished_at or time.time()
        return {
            "id": self.id,
            "status": self.status,
            "stage": self.stage,
            "chunk_index": self.chunk_index,
            "chunk_total": self.chunk_total,
            "current_text": self.current_text,
            "error": self.error,
            "generation": self.generation,
            "elapsed_s": round(end - self.started_at, 1),
        }


def _friendly_error(exc: Exception) -> str:
    msg = str(exc)
    if "out of memory" in msg.lower() or "MPS backend out of memory" in msg:
        return "Bellek yetersiz. Diğer uygulamaları kapatıp tekrar deneyin veya metni kısaltın."
    return f"Ses üretimi sırasında hata oluştu ({type(exc).__name__}): {msg[:300]}"


class JobManager:
    def __init__(self, engine, storage: Storage):
        self._engine = engine
        self._storage = storage
        self._lock = threading.Lock()
        self._current: Job | None = None

    @property
    def current(self) -> Job | None:
        return self._current

    def get(self, job_id: str) -> Job | None:
        job = self._current
        return job if job and job.id == job_id else None

    def start(self, req: GenerateRequest, reference_path: Path | None, profile_name: str | None) -> Job:
        if self._engine.status != "ready":
            raise EngineNotReadyError()
        with self._lock:
            if self._current and self._current.status == "running":
                raise BusyError()
            job = Job(id=new_id())
            self._current = job
        threading.Thread(
            target=self._run, args=(job, req, reference_path, profile_name), daemon=True, name=f"job-{job.id[:8]}"
        ).start()
        return job

    def cancel(self, job_id: str) -> bool:
        job = self.get(job_id)
        if not job or job.status != "running":
            return False
        job.cancel_requested = True
        job.stage = "İptal ediliyor (mevcut parça bitince durur)"
        return True

    def _run(self, job: Job, req: GenerateRequest, reference_path: Path | None, profile_name: str | None) -> None:
        engine = self._engine
        try:
            chunks = prepare_chunks(req.text)
            job.chunk_total = len(chunks)
            engine.set_seed(req.settings.seed)
            if reference_path:
                job.stage = "Referans ses analiz ediliyor"
            engine.prepare_voice(reference_path, req.settings)

            pieces = []
            for i, chunk in enumerate(chunks, start=1):
                if job.cancel_requested:
                    job.status, job.stage = "cancelled", "İptal edildi"
                    return
                job.chunk_index, job.current_text, job.stage = i, chunk.text, "Seslendiriliyor"
                pieces.append(engine.synthesize(chunk.text, req.settings))

            job.stage = "Parçalar birleştiriliyor"
            sr = engine.sample_rate
            pauses = [round(req.settings.pause_ms * c.pause_factor) for c in chunks[:-1]]
            wav = audio.limit_peak(audio.concat_with_pauses(pieces, sr, pauses))
            gen_id = new_id()
            audio.write_wav(config.GENERATIONS_DIR / f"{gen_id}.wav", wav, sr)
            job.generation = self._storage.add_generation({
                "id": gen_id,
                "text": req.text,
                "profile_id": req.profile_id,
                "profile_name": profile_name,
                "reference_id": req.reference_id,
                "settings": req.settings.model_dump(),
                "chunks": len(chunks),
                "duration_s": len(wav) / sr,
                "gen_seconds": time.time() - job.started_at,
                "device": engine.device or "unknown",
            })
            job.status, job.stage = "done", "Tamamlandı"
        except Exception as exc:
            log.exception("Generation failed")
            job.status, job.stage, job.error = "error", "Hata", _friendly_error(exc)
        finally:
            job.finished_at = time.time()
            job.current_text = ""
            try:
                engine.release_cache()
            except Exception:
                log.exception("Cache release failed")
