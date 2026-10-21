"""Chatterbox Multilingual V3 wrapper. The model is loaded once and kept in memory."""
import logging
import threading
from collections import OrderedDict
from pathlib import Path

import numpy as np

from . import config
from .schemas import GenerationSettings

log = logging.getLogger("iesoft.engine")

_CONDS_CACHE_SIZE = 4


def _patch_turkish_capitalisation() -> None:
    """Chatterbox's punc_norm capitalises the first letter with str.upper(): "ışık" → "Işık",
    which its tokenizer then lowercases to "işık". Keep a leading dotless ı intact."""
    import chatterbox.mtl_tts as mtl

    original = mtl.punc_norm
    if getattr(original, "_iesoft_patched", False):
        return

    def punc_norm(text: str) -> str:
        out = original(text)
        return "ı" + out[1:] if text[:1] == "ı" and out[:1] == "I" else out

    punc_norm._iesoft_patched = True
    mtl.punc_norm = punc_norm


class ChatterboxEngine:
    def __init__(self) -> None:
        self.status = "idle"  # idle | loading | ready | error
        self.device: str | None = None
        self.error: str | None = None
        self.sample_rate = 24000
        self._model = None
        self._default_conds = None
        self._conds_cache: OrderedDict[str, object] = OrderedDict()
        self._lock = threading.Lock()

    def load(self) -> None:
        with self._lock:
            if self.status in ("loading", "ready"):
                return
            self.status = "loading"
        try:
            import torch
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            _patch_turkish_capitalisation()

            device = config.DEVICE
            if device == "auto":
                device = "mps" if torch.backends.mps.is_available() else "cpu"
            try:
                model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model=config.T3_MODEL)
            except RuntimeError:
                if device != "mps":
                    raise
                log.exception("MPS load failed, falling back to CPU")
                device = "cpu"
                model = ChatterboxMultilingualTTS.from_pretrained(device=device, t3_model=config.T3_MODEL)
            self._model = model
            self._default_conds = model.conds
            self.sample_rate = model.sr
            self.device = device
            self.status = "ready"
            log.info("Chatterbox V3 ready on %s", device)
        except Exception as exc:  # surfaced to the UI via /api/status
            log.exception("Model load failed")
            self.error = f"{type(exc).__name__}: {exc}"
            self.status = "error"

    def set_seed(self, seed: int) -> None:
        import torch

        torch.manual_seed(seed)

    def _conds_for(self, reference_path: Path | None, exaggeration: float):
        if reference_path is None:
            return self._default_conds
        key = str(reference_path)
        if key in self._conds_cache:
            self._conds_cache.move_to_end(key)
            return self._conds_cache[key]
        self._model.prepare_conditionals(key, exaggeration=exaggeration)
        self._conds_cache[key] = self._model.conds
        if len(self._conds_cache) > _CONDS_CACHE_SIZE:
            self._conds_cache.popitem(last=False)
        return self._model.conds

    def prepare_voice(self, reference_path: Path | None, settings: GenerationSettings) -> None:
        self._model.conds = self._conds_for(reference_path, settings.exaggeration)

    def synthesize(self, text: str, settings: GenerationSettings) -> np.ndarray:
        wav = self._model.generate(
            text,
            language_id=config.LANGUAGE_ID,
            exaggeration=settings.exaggeration,
            cfg_weight=settings.cfg_weight,
            temperature=settings.temperature,
            repetition_penalty=settings.repetition_penalty,
        )
        return wav.squeeze(0).numpy().astype(np.float32)

    def release_cache(self) -> None:
        if self.device == "mps":
            import torch

            torch.mps.empty_cache()
