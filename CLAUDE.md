# CLAUDE.md — IESOFT Voice Studio

Lokal Türkçe TTS stüdyosu: Chatterbox Multilingual V3 (MPS) + FastAPI + React/Tailwind. Kullanıcı Türkçe konuşur; yanıtlar Türkçe.

## Yeni makinede ayağa kaldırma
1. Gereksinimleri kontrol et: Apple Silicon, Python 3.13 (`python3.13`), Node 20+, `ffmpeg`, `git`, ≥6 GB boş disk (`df -h`).
2. Model indirmesi ~3,2 GB — indirmeden önce kullanıcıya bildir ve onay al.
3. `scripts/setup.sh` (modelsiz: `SKIP_MODEL=1 scripts/setup.sh`).
4. `scripts/launch.sh` → `http://127.0.0.1:8765`, `/api/status` içinde `model.status == "ready"` bekle.
5. Doğrula: `.venv/bin/python -m unittest discover -s backend/tests -t .` ve arayüzde kısa bir üretim.

## Kurallar
- Kalıcı kurallar: `docs/KAIDE.md` — özellikle MPS watermark ayarları ve sabit paket sürümleri.
- `.venv` paketlerini ve Chatterbox commit'ini (`5de7a54`) izinsiz güncelleme; yeni model indirme onaysız yapılmaz.
- `data/` (ses kayıtları, profiller, geçmiş) ve `outputs/` depoya girmez.
- Model desteklemediği özelliği varmış gibi gösterme; sesi dinleyemediğini açıkça belirt, telaffuz kararını kullanıcıya bırak.
- Değişiklikten sonra: ilgili testler + `FEATURES.md`, `TEST_CASES.md`, `CHANGELOG.md`, `PROGRESS.md` güncelle.

## Önemli dosyalar
- `backend/app/turkish_normalizer.py` — sayı/%/tarih/kısaltma → Türkçe kelime (kısaltmalar bitişik: "ABD'de" → "abedede", kullanıcı dinleyerek seçti)
- `backend/app/text_splitter.py` — ~200 karakterlik cümle gruplama, noktalamaya göre duraklama
- `backend/app/tts_engine.py` — model tek sefer yüklenir; `punc_norm` Türkçe büyük harf yaması
- `backend/app/config.py` — MPS bellek sınırı, limitler

## Bilinen durum
- Varsayılan ses (`conds.pt`) İngilizce konuşmacı → hafif yabancı aksan. Kalıcı çözüm: izinli Türkçe anadil referans sesi.
- Kullanıcının beğendiği ayarlar: hız uygun, gruplu parçalama daha akıcı bulundu (21.10.2026).
