"""Compare generation presets with the model's built-in voice (no reference audio).

Uses the same pipeline as the web app (sentence chunking, seed, pauses, peak limit).
Usage: .venv/bin/python scripts/compare_presets.py
Stop the web server first so the model is not loaded twice.
"""
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import audio, config  # noqa: E402  (config sets MPS env before torch)
from backend.app.schemas import GenerationSettings  # noqa: E402
from backend.app.text_splitter import prepare_chunks  # noqa: E402
from backend.app.tts_engine import ChatterboxEngine  # noqa: E402

TEXT = (
    "Bir zamanlar uzak bir şehirde yaşayan yaşlı bir adam vardı. "
    "Her sabah güneş doğmadan uyanır ve sessizce dua ederdi. "
    "Bir gün küçük bir çocuk ona sordu: Neden her sabah dua ediyorsun? "
    "Yaşlı adam gülümsedi ve cevap verdi: "
    "Çünkü umut, insanın kalbinde hiç sönmemesi gereken bir ışıktır."
)
SEED = 42
PRESETS = {
    "dogal": dict(exaggeration=0.5, cfg_weight=0.5, temperature=0.7, repetition_penalty=1.2),
    "duygusal": dict(exaggeration=0.7, cfg_weight=0.3, temperature=0.7, repetition_penalty=1.3),
    "dramatik": dict(exaggeration=0.8, cfg_weight=0.3, temperature=0.8, repetition_penalty=1.4),
}
MAX_TOKEN_AUDIO_S = 1000 * 0.04  # T3 max_new_tokens=1000 at 25 tokens/s


def longest_silence(wav, sr: int, threshold: float = 0.01) -> float:
    frame = int(0.02 * sr)
    best = run = 0
    for i in range(0, len(wav) - frame, frame):
        quiet = float((wav[i:i + frame] ** 2).mean()) ** 0.5 < threshold
        run = run + 1 if quiet else 0
        best = max(best, run)
    return best * 0.02


def main() -> int:
    out_dir = PROJECT_ROOT / "outputs" / "presets"
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = ChatterboxEngine()
    t0 = time.perf_counter()
    engine.load()
    if engine.status != "ready":
        print("Model yüklenemedi:", engine.error)
        return 1
    conds = engine._default_conds
    print(f"model ready on {engine.device} in {time.perf_counter() - t0:.1f}s")
    print(f"built-in voice (conds.pt) loaded: {conds is not None}"
          + (f" | speaker_emb {tuple(conds.t3.speaker_emb.shape)}" if conds is not None else ""))
    if conds is None:
        return 1

    chunks = prepare_chunks(TEXT)
    print(f"{len(chunks)} chunks:", *[f"  [{i}] {c.text}" for i, c in enumerate(chunks, 1)], sep="\n")

    report = {"text": TEXT, "seed": SEED, "device": engine.device, "chunks": [c.text for c in chunks], "presets": {}}
    for name, params in PRESETS.items():
        settings = GenerationSettings(**params, seed=SEED, pause_ms=400)
        engine.set_seed(SEED)
        engine.prepare_voice(None, settings)
        pieces, rows = [], []
        t_preset = time.perf_counter()
        for i, chunk in enumerate(chunks, 1):
            t = time.perf_counter()
            wav = engine.synthesize(chunk.text, settings)
            gen_s = time.perf_counter() - t
            dur = len(wav) / engine.sample_rate
            rows.append({
                "chunk": i, "chars": len(chunk.text), "audio_s": round(dur, 2), "gen_s": round(gen_s, 1),
                "chars_per_s": round(len(chunk.text) / dur, 1) if dur else None,
                "longest_pause_s": round(longest_silence(wav, engine.sample_rate), 2),
                "hit_token_limit": dur >= MAX_TOKEN_AUDIO_S - 0.5,
            })
            pieces.append(wav)
            print(f"{name} chunk {i}: {rows[-1]}", flush=True)
        total_gen = time.perf_counter() - t_preset
        pauses = [round(settings.pause_ms * c.pause_factor) for c in chunks[:-1]]
        full = audio.limit_peak(audio.concat_with_pauses(pieces, engine.sample_rate, pauses))
        path = out_dir / f"preset_{name}_seed{SEED}.wav"
        audio.write_wav(path, full, engine.sample_rate)
        engine.release_cache()
        report["presets"][name] = {
            "settings": settings.model_dump(), "file": str(path.relative_to(PROJECT_ROOT)),
            "audio_s": round(len(full) / engine.sample_rate, 2), "gen_s": round(total_gen, 1), "chunks": rows,
        }
        print(f"== {name}: {report['presets'][name]['audio_s']}s audio in {total_gen:.1f}s -> {path.name}", flush=True)

    (out_dir / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
