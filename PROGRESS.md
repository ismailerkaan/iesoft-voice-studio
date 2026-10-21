# IESOFT Voice Studio — İlerleme

## 14.10.2026 — Kurulum ve ilk V3 testi

**Ortam**
- `.venv`: Python 3.13.5, torch 2.6.0, transformers 5.2.0
- `chatterbox-tts` resmî depodan `5de7a54aa4e5e2baadb0182dde554908b48b85c2` commit'ine sabitli (PyPI 0.1.7 V3 içermiyor)
- Tam bağımlılık listesi: `requirements.lock.txt`
- Model: `ResembleAI/chatterbox` → `t3_mtl23ls_v3.safetensors`, `s3gen.pt`, `ve.pt`, tokenizer JSON'ları (~3,2 GB, `~/.cache/huggingface/hub`)

**Kararlar**
- MPS'te `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5`, `PYTORCH_MPS_LOW_WATERMARK_RATIO=0.3` zorunlu.
  Sınırsızken T3 üretimi sırasında MPS ayırıcısı ~16,6 GB'a şişiyor (canlı tensör ~3 GB), sistem swap'a düşüyor.
  Sınır çıktıyı değiştirmiyor (aynı seed ile bit düzeyinde aynı WAV), üretimi ~2 kat hızlandırıyor.
- MPS (sınırlı) > CPU > MPS (sınırsız) — kısa cümlede: 27,9 sn / 45,7 sn / 69,0 sn.
- `PYTORCH_ENABLE_MPS_FALLBACK=1` açık; testte CPU'ya düşen işlem uyarısı görülmedi.

**Açık noktalar / sonraki adımlar (onay bekliyor)**
- Telaffuz ve doğallık henüz insan kulağıyla değerlendirilmedi.
- Referans ses verilmedi; model içindeki varsayılan (`conds.pt`) ses kullanıldı. Türkçe referans sesle klonlama test edilmeli.
- Tepe seviyesi 0,992 — ileride loudness normalizasyonu (pyloudnorm / FFmpeg `loudnorm`) gerekli.
- Cümle arası duraklamalar kısa (yalnızca 1 adet ≥0,3 sn) — cümle bazlı bölme + kontrollü sessizlik planlanmalı.

## 14.10.2026 — Web arayüzü MVP (v0.1.0)
- FastAPI + React/Tailwind arayüz, `scripts/run_studio.sh` → `http://127.0.0.1:8765`. Python ortamına paket eklenmedi (FastAPI/uvicorn zaten kuruluydu).
- Gerçek ölçüm (MPS, varsayılan ses, 4 parça): 100,5 sn üretim → 19,16 sn ses. Süreç bellek ayak izi en fazla ~7,4 GB.
- Model açılışta ~20 sn'de yükleniyor, sonra bellekte kalıyor.
- Sonraki adım önerileri (onay bekliyor): kulakla kalite değerlendirmesi, gerçek Türkçe referans sesle klonlama testi, LUFS normalizasyonu.

## 14.10.2026 — Referanssız (yerleşik ses) preset karşılaştırması
- Referans ses zorunlu değil: `conds.pt` (yerleşik anlatıcı) yükleniyor, `speaker_emb (1, 256)`. Arayüzde "Varsayılan ses (referanssız)" seçeneği ve açıklama kutusu görünür hâle getirildi.
- `scripts/compare_presets.py` (web ile aynı hat; seed 42, 4 parça). Çıktılar: `outputs/presets/`, ayrıntı `outputs/presets/report.json`.
- Sonuç (ses / üretim): Doğal 18,28 / 130,6 sn · Duygusal 19,56 / 133,0 sn · Dramatik 19,72 / 189,0 sn. Hiçbir parça token sınırına ulaşmadı.
- Hız anomalileri (≈15 karakter/sn normal): Doğal parça 4 = 19,1 kr/sn (olası yutulan kelime); Dramatik parça 2 = 12,5 kr/sn (olası uzatma/tekrar). Kelime düzeyi doğrulama için ASR yok — kulakla kontrol gerekli.
- Ölçüm sırasında sistemde ağır swap vardı (Termius Helper ~30 GB, swap ~22,5 GB) → süreler önceki testlerden yavaş.

## 14.10.2026 — Aksan araştırması ve CFG testi (A=0,0 / B=0,2 / C=0,5)
- `language_id="tr"` doğru iletiliyor: `config.LANGUAGE_ID` → `engine.synthesize` → tokenizer metnin başına `[tr]` ekliyor. Test metninde bilinmeyen token yok.
- **Bulgu (düzeltilmedi, onay bekliyor):** Chatterbox tokenizer Python `str.lower()` kullanıyor → `I`→`i` (doğrusu `ı`), `İ`→`i̇`. "Işık", "IRMAK", büyük harfli başlıklar yanlış okunabilir. Öneri: backend'de Türkçe kurallı küçük harfe çevirme (I→ı, İ→i) metni modele vermeden önce.
- `conds.pt` İngilizce Chatterbox'ın varsayılan sesiyle aynı dosya (SHA256 6552d705…, iki snapshot'ta ortak) → yerleşik ses İngilizce konuşmacıdan geliyor. Etki üç yerde: T3 konuşma istemi (150 token ≈ 6 sn), S3Gen akustik istem (314 mel kare) ve konuşmacı vektörleri. CFG yalnızca T3'ü etkiler; S3Gen istemi değişmez.
- Resmî README: referans sesin dili etiketle uyuşmuyorsa aksan aktarılabilir, azaltmak için `cfg_weight=0`.
- Ölçümler (seed 42, exag 0,5, temp 0,7, rep 1,2): A 10,96 sn ses / 79,1 sn üretim (sunucunun ilk işi, ısınma dahil) · B 10,92 / 43,6 sn · C 10,04 / 39,2 sn. Hız: A ve B 13,1–13,9 kr/sn (dengeli), C 13,5–15,7 kr/sn (daha hızlı). Çıktılar `outputs/cfg_test/`.

## 21.10.2026 — Türkçe akıcılık iyileştirmesi (A: normalleştirme, B: akıcı parçalama) — v0.2.0
- Analiz: "Yapay zekâ…" (55 sn) metninde `%50`, `700`, `2030'da`, `ABD'de` ham hâliyle modele gidiyordu; metin 14 tek cümlelik parçaya bölünüyordu, her parça başında/sonunda ~0,5 sn ölü sessizlik (toplam ~13 sn) vardı.
- Uygulandı: `turkish_normalizer.py`, gruplu `split_chunks` (hedef 200, maks 280 karakter), noktalamaya göre duraklama, `punc_norm` Türkçe büyük harf yaması, `/api/text/split` normalleştirilmiş metni gösterir.
- A/B (aynı metin, aynı ayar, seed 42; `outputs/ab_test/`): önce 14 parça / 55,0 sn ses / aktif konuşma 36,8 sn (20,1 kr/sn net) → sonra 6 parça / 46,1 sn ses / aktif 34,5 sn (22,3 kr/sn net), iç doğal duraklama 2 → 6. Üretim 158,7 sn.
- Risk: net konuşma ~%11 hızlandı — daha akıcı okuma ya da uzun parçada kelime atlama olabilir; ASR olmadan ayırt edilemez → kulakla kontrol gerekli. Hızlı gelirse: CFG 0,3 veya `TARGET_CHUNK_CHARS` 150.
- Değişmeyen kök sorun: varsayılan ses İngilizce konuşmacı → aksan için Türkçe referans ses gerekli.
