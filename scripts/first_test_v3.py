"""IESOFT Voice Studio - Chatterbox Multilingual V3 first Turkish smoke test.

Usage: .venv/bin/python scripts/first_test_v3.py [--device mps|cpu] [--out PATH]
"""
import argparse
import os
import resource
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
# Without a cap, the MPS caching allocator grows to ~16 GB during T3 autoregressive
# decoding (live tensors stay ~3 GB) and pushes a 16 GB M1 into heavy swap.
os.environ.setdefault("PYTORCH_MPS_HIGH_WATERMARK_RATIO", "0.5")
os.environ.setdefault("PYTORCH_MPS_LOW_WATERMARK_RATIO", "0.3")

import soundfile as sf
import torch

from chatterbox.mtl_tts import ChatterboxMultilingualTTS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TEXT = (
    "Bir zamanlar, uzak bir şehirde yaşayan yaşlı bir adam vardı. "
    "Her sabah güneş doğmadan uyanır, sessizce dua ederdi. "
    "Bir gün küçük bir çocuk ona sordu: Neden her sabah dua ediyorsun? "
    "Yaşlı adam gülümsedi ve cevap verdi: "
    "Çünkü umut, insanın kalbinde hiç sönmemesi gereken bir ışıktır."
)
SEED = 42


def peak_rss_gb() -> float:
    # macOS reports ru_maxrss in bytes
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024**3


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--device", default="mps", choices=["mps", "cpu"])
    parser.add_argument("--out", default=str(PROJECT_ROOT / "outputs" / "first_test_v3.wav"))
    args = parser.parse_args()

    torch.manual_seed(SEED)
    print(f"torch {torch.__version__} | device={args.device} | mps_available={torch.backends.mps.is_available()}")
    print(f"mps watermark high={os.environ['PYTORCH_MPS_HIGH_WATERMARK_RATIO']} low={os.environ['PYTORCH_MPS_LOW_WATERMARK_RATIO']}")

    t0 = time.perf_counter()
    model = ChatterboxMultilingualTTS.from_pretrained(device=args.device, t3_model="v3")
    load_s = time.perf_counter() - t0
    print(f"model loaded in {load_s:.1f}s | model.device={model.device} | peak RSS {peak_rss_gb():.2f} GB")

    t1 = time.perf_counter()
    wav = model.generate(TEXT, language_id="tr")
    if args.device == "mps":
        torch.mps.synchronize()
    gen_s = time.perf_counter() - t1

    audio = wav.squeeze(0).detach().cpu().numpy()
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out, audio, model.sr, subtype="PCM_16")
    dur = len(audio) / model.sr

    print(f"generation {gen_s:.1f}s | audio {dur:.2f}s | RTF {gen_s / dur:.2f} | sr {model.sr}")
    print(f"peak RSS {peak_rss_gb():.2f} GB")
    if args.device == "mps":
        print(f"mps driver allocated {torch.mps.driver_allocated_memory() / 1024**3:.2f} GB")
    print(f"saved {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
