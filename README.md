# IESOFT Voice Studio

Apple Silicon Mac üzerinde **tamamen lokal** çalışan Türkçe seslendirme stüdyosu.
Model: [Chatterbox Multilingual V3](https://github.com/resemble-ai/chatterbox) (Resemble AI, MIT).
Arayüz: FastAPI + React/Tailwind, `http://127.0.0.1:8765`.

Özellikler: Türkçe metin normalleştirme (sayı, %, tarih, saat, para, kısaltma, I/İ), akıcı cümle gruplama,
referans sesle klonlama (izin onaylı), ses profilleri, geçmiş, WAV/MP3 indirme. Ayrıntı: [FEATURES.md](FEATURES.md).

---

## Gereksinimler

| | Sürüm / not |
|---|---|
| Donanım | Apple Silicon (M1 ve üzeri), **en az 16 GB RAM** (model + MPS ≈ 4–7 GB) |
| İşletim sistemi | macOS 13+ (MPS için 12.3+; test: macOS 26.5) |
| Disk | **≈ 6 GB boş alan**: model 3,2 GB + Python ortamı 1,2 GB + node_modules 125 MB + pay |
| Python | **3.13** (`brew install python@3.13`). 3.14 desteklenmez (torch 2.6.0 yok) |
| Node.js | 20+ (`brew install node`) — test: 24.4 |
| FFmpeg | MP3 dönüşümü için (`brew install ffmpeg`) |
| git | Chatterbox paketi GitHub'dan sabit commit ile kurulur |
| İnternet | Yalnızca kurulumda (paketler + model). Sonrası tamamen çevrimdışı çalışır |

## Hızlı kurulum

```bash
git clone https://github.com/ismailerkaan/iesoft-voice-studio.git
cd iesoft-voice-studio
scripts/setup.sh
```

`setup.sh` sırasıyla: `.venv` (Python 3.13) oluşturur → `requirements.lock.txt` ile **sabit sürümleri** kurar →
web arayüzünü derler (`npm ci && npm run build`) → model dosyalarını indirir (~3,2 GB) → testleri çalıştırır.
Modeli kurulumda indirmek istemezseniz: `SKIP_MODEL=1 scripts/setup.sh` (ilk açılışta otomatik iner).

## Çalıştırma

```bash
scripts/launch.sh
```

Sunucuyu başlatır, model hazır olunca (~20 sn; ilk kez indiriliyorsa daha uzun) tarayıcıyı açar.
Zaten çalışıyorsa sadece tarayıcıyı açar. Durdurmak: `Ctrl + C`.
Yalnızca sunucu: `scripts/run_studio.sh`.

**İsteğe bağlı kısayol** — `~/.zshrc` sonuna ekleyin (yolu kendi klon konumunuza göre değiştirin), sonra `iesoft voice`:

```zsh
iesoft() {
  case "${1:-}" in
    voice) "$HOME/development/python/iesoft-voice-studio/scripts/launch.sh" ;;
    *) echo "Kullanım: iesoft voice" ;;
  esac
}
```

## Model dosyaları

Hugging Face deposu `ResembleAI/chatterbox`, standart önbellek `~/.cache/huggingface/hub` (değiştirmek için `HF_HOME`).
Elle indirme: `.venv/bin/python scripts/download_model.py`

| Dosya | Boyut | Görev |
|---|---|---|
| `t3_mtl23ls_v3.safetensors` | 2,1 GB | V3 çok dilli metin → konuşma token modeli |
| `s3gen.pt` | 1,1 GB | Token → ses (vocoder) |
| `ve.pt` | 5,7 MB | Konuşmacı (ses) kodlayıcı |
| `conds.pt` | 0,1 MB | Yerleşik varsayılan ses (İngilizce konuşmacı — Türkçede hafif aksan verir) |
| `grapheme_mtl_merged_expanded_v1.json`, `Cangjie5_TC.json` | 2 MB | Tokenizer |

Test edilen HF snapshot: `5bb1f6ee58e50c3b8d408bc82a6d3740c2db6e18`.
Ses kayıtları, profiller ve üretilen sesler **depoya dahil değildir** (`data/`, `outputs/` gitignore'da).

## Sabit sürümler (değiştirmeyin)

- `chatterbox-tts` → GitHub `resemble-ai/chatterbox@5de7a54` (PyPI 0.1.7 V3 içermez)
- `torch==2.6.0`, `torchaudio==2.6.0`, `transformers==5.2.0`, `numpy` 2.x — tamamı `requirements.lock.txt`
- Frontend: `frontend/package-lock.json` (`npm ci`)

## Proje yapısı

```
backend/app/        FastAPI API, üretim işçisi, Chatterbox motoru, Türkçe normalleştirme, parçalama
backend/tests/      unittest (sahte motor; model gerektirmez)
frontend/           React + Tailwind arayüz (derlenmiş hali FastAPI tarafından sunulur)
scripts/            setup.sh, launch.sh, run_studio.sh, download_model.py, test/karşılaştırma betikleri
docs/KAIDE.md       kalıcı kurallar
```
Mimari: [ARCHITECTURE.md](ARCHITECTURE.md) · Güvenlik: [SECURITY.md](SECURITY.md) · Testler: [TEST_CASES.md](TEST_CASES.md) · İlerleme: [PROGRESS.md](PROGRESS.md)

## Testler

```bash
.venv/bin/python -m unittest discover -s backend/tests -t .
cd frontend && npm run typecheck
```

## Sorun giderme

| Belirti | Çözüm |
|---|---|
| Üretim çok yavaş, sistem swap'a düşüyor | `backend/app/config.py` içindeki `PYTORCH_MPS_HIGH/LOW_WATERMARK_RATIO` ayarları silinmemeli; ağır uygulamaları kapatın |
| `RuntimeError: invalid low watermark ratio` | HIGH ve LOW birlikte ayarlanmalı |
| "8765 portu kullanılıyor" | `lsof -i :8765` ile süreci bulun veya `PORT=8766 scripts/launch.sh` |
| MPS yok / hata | `IESOFT_DEVICE=cpu scripts/launch.sh` (daha yavaş) |
| MP3 indirme hatası | `ffmpeg` kurulu mu: `ffmpeg -version` |
| Model indirilemiyor | İnternet / Hugging Face erişimi; gerekirse `HF_TOKEN` tanımlayın |

## Lisans ve kullanım

- Chatterbox: MIT. Her üretilen seste Resemble AI **Perth filigranı** (duyulmaz) bulunur.
- Referans ses yalnızca sahibinin **kullanım ve klonlama izni** varsa yüklenmelidir (arayüz onay ister).
- Bu deponun kendi lisansı henüz belirlenmedi.
