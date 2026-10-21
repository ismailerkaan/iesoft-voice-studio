"""Central configuration. Imported before torch so MPS env vars take effect."""
import os
from pathlib import Path

# Without a cap the MPS caching allocator grows to ~16 GB during T3 decoding on a
# 16 GB M1 and pushes the system into swap (see PROGRESS.md, 14.10.2026).
os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.5")
os.environ.setdefault("PYTORCH_MPS_LOW_WATERMARK_RATIO", "0.3")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("IESOFT_DATA_DIR", PROJECT_ROOT / "data"))
REFERENCES_DIR = DATA_DIR / "references"
GENERATIONS_DIR = DATA_DIR / "generations"
DB_PATH = DATA_DIR / "studio.db"
FRONTEND_DIST = PROJECT_ROOT / "frontend" / "dist"

DEVICE = os.environ.get("IESOFT_DEVICE", "auto")  # auto | mps | cpu
T3_MODEL = "v3"
LANGUAGE_ID = "tr"

MAX_TEXT_CHARS = 5000
TARGET_CHUNK_CHARS = 200  # sentences are grouped up to this length for natural prosody
MAX_CHUNK_CHARS = 280
MIN_CHUNK_CHARS = 20

MAX_REFERENCE_BYTES = 25 * 1024 * 1024
MIN_REFERENCE_SECONDS = 3.0
MAX_REFERENCE_SECONDS = 60.0

MP3_BITRATE = "160k"  # MPEG-2 Layer III maximum at the model's 24 kHz sample rate


def ensure_dirs() -> None:
    for d in (DATA_DIR, REFERENCES_DIR, GENERATIONS_DIR):
        d.mkdir(parents=True, exist_ok=True)
