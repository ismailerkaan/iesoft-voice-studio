"""API tests with a fake TTS engine (no model, no torch)."""
import io
import shutil
import tempfile
import threading
import time
import unittest
from pathlib import Path

import numpy as np
import soundfile as sf
from fastapi.testclient import TestClient

from backend.app import config
from backend.app.main import create_app
from backend.app.storage import Storage


class FakeEngine:
    def __init__(self, delay: float = 0.0, fail: bool = False):
        self.status, self.device, self.error, self.sample_rate = "ready", "fake", None, 24000
        self.delay, self.fail = delay, fail
        self.calls: list[str] = []
        self.release = threading.Event()
        self.release.set()

    def load(self):
        pass

    def set_seed(self, seed):
        self.seed = seed

    def prepare_voice(self, reference_path, settings):
        self.reference_path = reference_path

    def synthesize(self, text, settings):
        self.release.wait(5)
        if self.fail:
            raise RuntimeError("MPS backend out of memory")
        self.calls.append(text)
        time.sleep(self.delay)
        return np.full(2400, 0.5, dtype=np.float32)

    def release_cache(self):
        pass


def wav_bytes(seconds: float, sr: int = 16000, silent: bool = False) -> bytes:
    t = np.arange(int(seconds * sr)) / sr
    data = np.zeros_like(t) if silent else 0.3 * np.sin(2 * np.pi * 220 * t)
    buf = io.BytesIO()
    sf.write(buf, data, sr, format="WAV")
    return buf.getvalue()


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self._orig = (config.DATA_DIR, config.REFERENCES_DIR, config.GENERATIONS_DIR)
        config.DATA_DIR, config.REFERENCES_DIR, config.GENERATIONS_DIR = (
            self.tmp, self.tmp / "references", self.tmp / "generations")
        config.ensure_dirs()
        self.engine = FakeEngine()
        app = create_app(engine=self.engine, storage=Storage(self.tmp / "t.db"), autoload=False)
        self.client = TestClient(app)
        self.client.__enter__()

    def tearDown(self):
        self.engine.release.set()
        self.client.__exit__(None, None, None)
        config.DATA_DIR, config.REFERENCES_DIR, config.GENERATIONS_DIR = self._orig
        shutil.rmtree(self.tmp)

    def wait_job(self, job_id: str) -> dict:
        for _ in range(200):
            job = self.client.get(f"/api/jobs/{job_id}").json()
            if job["status"] != "running":
                return job
            time.sleep(0.02)
        self.fail("job did not finish")

    def upload(self, data: bytes, consent: str = "true", name: str = "ses.wav"):
        return self.client.post("/api/references", files={"file": (name, data, "audio/wav")}, data={"consent": consent})

    # --- generation
    def test_generate_full_flow_with_chunks_history_and_downloads(self):
        # Two paragraphs → two chunks, with a doubled pause between them.
        text = "Bir zamanlar yaşlı bir adam vardı. Her sabah dua ederdi.\n\nBir gün %50 ihtimalle yağmur yağdı."
        r = self.client.post("/api/generate", json={"text": text, "settings": {"seed": 7, "pause_ms": 100}})
        self.assertEqual(r.status_code, 202, r.text)
        job = self.wait_job(r.json()["id"])
        self.assertEqual(job["status"], "done", job)
        self.assertEqual(job["chunk_total"], 2)
        self.assertEqual(self.engine.seed, 7)
        gen = job["generation"]
        self.assertAlmostEqual(gen["duration_s"], (2400 * 2 + 2 * 2400) / 24000, places=2)
        self.assertIn("yüzde elli", self.engine.calls[1])
        self.assertEqual(gen["settings"]["seed"], 7)

        history = self.client.get("/api/generations").json()
        self.assertEqual([h["id"] for h in history], [gen["id"]])

        wav = self.client.get(f"/api/generations/{gen['id']}/audio")
        self.assertEqual(wav.status_code, 200)
        self.assertEqual(wav.headers["content-type"], "audio/wav")
        mp3 = self.client.get(f"/api/generations/{gen['id']}/audio?format=mp3&download=true")
        self.assertEqual(mp3.status_code, 200, mp3.text)
        self.assertEqual(mp3.headers["content-type"], "audio/mpeg")
        self.assertIn("attachment", mp3.headers["content-disposition"])
        self.assertIn(".mp3", mp3.headers["content-disposition"])

    def test_only_one_generation_at_a_time(self):
        self.engine.release.clear()
        first = self.client.post("/api/generate", json={"text": "Birinci uzun bir metin cümlesi."})
        self.assertEqual(first.status_code, 202)
        second = self.client.post("/api/generate", json={"text": "İkinci uzun bir metin cümlesi."})
        self.assertEqual(second.status_code, 409)
        self.assertIn("başka bir seslendirme", second.json()["detail"])
        self.engine.release.set()
        self.assertEqual(self.wait_job(first.json()["id"])["status"], "done")

    def test_cancel_between_chunks(self):
        self.engine.release.clear()
        text = " ".join(f"Bu {i}. cümle yeterince uzun bir cümledir." for i in range(1, 6))
        job_id = self.client.post("/api/generate", json={"text": text}).json()["id"]
        self.assertEqual(self.client.post(f"/api/jobs/{job_id}/cancel").status_code, 200)
        self.engine.release.set()
        job = self.wait_job(job_id)
        self.assertEqual(job["status"], "cancelled")
        self.assertLess(len(self.engine.calls), 5)
        self.assertEqual(self.client.get("/api/generations").json(), [])

    def test_engine_error_is_user_friendly(self):
        self.engine.fail = True
        job_id = self.client.post("/api/generate", json={"text": "Hata testi için bir cümle."}).json()["id"]
        job = self.wait_job(job_id)
        self.assertEqual(job["status"], "error")
        self.assertIn("Bellek yetersiz", job["error"])

    def test_model_not_ready(self):
        self.engine.status = "loading"
        r = self.client.post("/api/generate", json={"text": "Merhaba dünya, nasılsın?"})
        self.assertEqual(r.status_code, 503)

    def test_validation_errors(self):
        self.assertEqual(self.client.post("/api/generate", json={"text": "   "}).status_code, 422)
        too_long = self.client.post("/api/generate", json={"text": "a" * (config.MAX_TEXT_CHARS + 1)})
        self.assertEqual(too_long.status_code, 422)
        bad = self.client.post("/api/generate", json={"text": "Merhaba.", "settings": {"cfg_weight": 5}})
        self.assertEqual(bad.status_code, 422)
        self.assertIn("cfg_weight", bad.json()["detail"])
        missing_ref = self.client.post("/api/generate", json={"text": "Merhaba.", "reference_id": "../../etc"})
        self.assertEqual(missing_ref.status_code, 404)

    # --- references
    def test_reference_upload_and_use(self):
        r = self.upload(wav_bytes(5))
        self.assertEqual(r.status_code, 201, r.text)
        ref = r.json()
        self.assertAlmostEqual(ref["duration_s"], 5.0, places=1)
        self.assertEqual(self.client.get(f"/api/references/{ref['id']}/audio").status_code, 200)
        job_id = self.client.post("/api/generate", json={"text": "Referanslı bir deneme cümlesi.", "reference_id": ref["id"]}).json()["id"]
        self.assertEqual(self.wait_job(job_id)["status"], "done")
        self.assertEqual(self.engine.reference_path, config.REFERENCES_DIR / f"{ref['id']}.wav")

    def test_reference_rejections(self):
        self.assertEqual(self.upload(wav_bytes(5), consent="false").status_code, 400)
        self.assertIn("en az", self.upload(wav_bytes(1)).json()["detail"])
        self.assertIn("en fazla", self.upload(wav_bytes(61, sr=8000)).json()["detail"])
        self.assertIn("sessiz", self.upload(wav_bytes(5, silent=True)).json()["detail"])
        self.assertIn("WAV", self.upload(b"not audio at all" * 100, name="x.wav").json()["detail"])
        self.assertEqual(list(config.REFERENCES_DIR.iterdir()), [])

    # --- profiles
    def test_profile_crud_and_duplicate_name(self):
        body = {"name": "Hikâye Anlatıcısı", "settings": {"exaggeration": 0.7}}
        created = self.client.post("/api/profiles", json=body)
        self.assertEqual(created.status_code, 201, created.text)
        pid = created.json()["id"]
        self.assertEqual(self.client.post("/api/profiles", json={"name": "hikâye anlatıcısı"}).status_code, 409)
        updated = self.client.put(f"/api/profiles/{pid}", json={**body, "settings": {"exaggeration": 1.1}})
        self.assertEqual(updated.json()["settings"]["exaggeration"], 1.1)
        self.assertEqual(self.client.delete(f"/api/profiles/{pid}").status_code, 204)
        self.assertEqual(self.client.get("/api/profiles").json(), [])
        self.assertEqual(self.client.delete("/api/profiles/not-an-id").status_code, 404)

    # --- security
    def test_cross_origin_write_blocked(self):
        r = self.client.post("/api/generate", json={"text": "Merhaba."}, headers={"Origin": "https://evil.example"})
        self.assertEqual(r.status_code, 403)
        ok = self.client.post("/api/text/split", json={"text": "Bir. İki."}, headers={"Origin": "http://localhost:5173"})
        self.assertEqual(ok.status_code, 200)

    def test_untrusted_host_header_rejected(self):
        self.assertEqual(self.client.get("/api/status", headers={"Host": "attacker.example"}).status_code, 400)


if __name__ == "__main__":
    unittest.main()
