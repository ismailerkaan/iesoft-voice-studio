"""Audio assembly, reference sanitising and MP3 export."""
import io
import subprocess
from collections.abc import Sequence
from pathlib import Path

import numpy as np
import soundfile as sf

from . import config

_FADE_MS = 8
_PEAK_CEILING = 10 ** (-1.0 / 20)  # -1 dBFS


class AudioError(ValueError):
    """User-facing audio validation error."""


def concat_with_pauses(chunks: list[np.ndarray], sr: int, pauses_ms: Sequence[int]) -> np.ndarray:
    """Join chunks; ``pauses_ms[i]`` is the silence inserted after ``chunks[i]``."""
    fade = int(sr * _FADE_MS / 1000)
    ramp = np.linspace(0.0, 1.0, fade, dtype=np.float32)
    parts: list[np.ndarray] = []
    for i, chunk in enumerate(chunks):
        c = chunk.astype(np.float32, copy=True)
        if len(c) > 2 * fade:  # short fades remove clicks at chunk edges
            c[:fade] *= ramp
            c[-fade:] *= ramp[::-1]
        if i:
            parts.append(np.zeros(int(sr * pauses_ms[i - 1] / 1000), dtype=np.float32))
        parts.append(c)
    return np.concatenate(parts) if parts else np.zeros(0, dtype=np.float32)


def limit_peak(audio: np.ndarray) -> np.ndarray:
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    return audio * (_PEAK_CEILING / peak) if peak > _PEAK_CEILING else audio


def write_wav(path: Path, audio: np.ndarray, sr: int) -> None:
    sf.write(path, audio, sr, subtype="PCM_16")


def sanitize_reference(data: bytes, dest: Path) -> float:
    """Validate an uploaded WAV and re-encode it as mono PCM16. Returns duration in seconds."""
    if len(data) > config.MAX_REFERENCE_BYTES:
        raise AudioError("Dosya çok büyük (en fazla 25 MB).")
    try:
        info = sf.info(io.BytesIO(data))
        if info.format != "WAV":
            raise AudioError("Yalnızca WAV dosyası yüklenebilir.")
        audio, sr = sf.read(io.BytesIO(data), dtype="float32", always_2d=True)
    except AudioError:
        raise
    except Exception as exc:
        raise AudioError("Dosya okunamadı; geçerli bir WAV dosyası olduğundan emin olun.") from exc

    duration = len(audio) / sr
    if duration < config.MIN_REFERENCE_SECONDS:
        raise AudioError(f"Referans ses en az {config.MIN_REFERENCE_SECONDS:.0f} saniye olmalı.")
    if duration > config.MAX_REFERENCE_SECONDS:
        raise AudioError(f"Referans ses en fazla {config.MAX_REFERENCE_SECONDS:.0f} saniye olmalı.")
    mono = audio.mean(axis=1)
    if float(np.max(np.abs(mono))) < 1e-3:
        raise AudioError("Referans ses sessiz görünüyor.")
    write_wav(dest, mono, sr)
    return duration


def wav_to_mp3(wav_path: Path, mp3_path: Path) -> None:
    tmp = mp3_path.with_suffix(".tmp.mp3")
    result = subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(wav_path),
         "-codec:a", "libmp3lame", "-b:a", config.MP3_BITRATE, str(tmp)],
        capture_output=True, text=True, timeout=120,
    )
    if result.returncode != 0:
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f"MP3 dönüşümü başarısız: {result.stderr.strip()[:300]}")
    tmp.replace(mp3_path)
