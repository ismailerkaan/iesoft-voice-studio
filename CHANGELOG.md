# Değişiklik Günlüğü

## 0.2.0 — 21.10.2026
- Harf harf okunan kısaltmalar bitişik yazılır ("ABD'de" → "abedede", kullanıcı dinleme testiyle seçildi); H harfi "ha" okunur (THY → "tehaye").
- Türkçe metin normalleştirme (`backend/app/turkish_normalizer.py`): sayılar, sıra sayıları, %, tarih, saat, para, birimler, Hz./s.a.v. gibi kısaltmalar, ABD/TBMM gibi harf harf okunan kısaltmalar, büyük I/İ düzeltmesi.
- Chatterbox `punc_norm` için Türkçe büyük harf yaması (cümle başındaki "ı" korunur).
- Akıcı parçalama: cümleler ~200 karaktere kadar gruplanır, paragraf sınırı aşılmaz; duraklama noktalamaya göre (paragraf ×2, "…" ×1,6, "?/!" ×1,25).
- Parça önizlemesi modelin okuyacağı normalleştirilmiş metni gösterir.

## 0.1.0 — 14.10.2026
- `iesoft voice` terminal komutu (`~/.zshrc` fonksiyonu → `scripts/launch.sh`): sunucuyu başlatır, model hazır olunca tarayıcıyı açar; çalışıyorsa yalnızca tarayıcıyı açar.
- FastAPI backend + React/Tailwind web arayüzü (MVP), `scripts/run_studio.sh` ile `127.0.0.1:8765`.
- Profiller, referans ses yükleme, geçmiş, WAV/MP3 indirme, cümle bazlı uzun metin üretimi, iptal.
- MPS bellek sınırı uygulama genelinde varsayılan.

## 0.0.1 — 14.10.2026
- İzole `.venv` (Python 3.13), Chatterbox `5de7a54`, V3 modeli, ilk Türkçe MPS testi (`scripts/first_test_v3.py`).
