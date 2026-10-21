"""Download Chatterbox Multilingual V3 weights (~3.2 GB) into the Hugging Face cache.

Optional: the web app downloads the same files on first start. Running this first makes
the first start fast and lets you check the download separately.
Usage: .venv/bin/python scripts/download_model.py
"""
from huggingface_hub import snapshot_download

REPO_ID = "ResembleAI/chatterbox"
# Same files ChatterboxMultilingualTTS.from_pretrained(t3_model="v3") requests (commit 5de7a54).
FILES = [
    "t3_mtl23ls_v3.safetensors",
    "s3gen.pt",
    "ve.pt",
    "conds.pt",
    "grapheme_mtl_merged_expanded_v1.json",
    "Cangjie5_TC.json",
]

if __name__ == "__main__":
    path = snapshot_download(repo_id=REPO_ID, repo_type="model", revision="main", allow_patterns=FILES)
    print(f"Model dosyaları hazır: {path}")
