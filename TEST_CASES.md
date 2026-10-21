# IESOFT Voice Studio — Test Senaryoları

## TC-001 — V3 Türkçe ilk üretim (MPS)
**Kurulum:** `.venv` hazır, V3 model dosyaları HF önbelleğinde.
**Adım:** `.venv/bin/python scripts/first_test_v3.py --device mps`
**Beklenen:**
- Çıkış kodu 0, `outputs/first_test_v3.wav` oluşur (24 kHz, mono, PCM16)
- Log'da `mps watermark high=0.5 low=0.3` ve `mps driver allocated` < 6 GB
- Süre ~16,8 sn (seed 42 ile tekrarlanabilir)
- Dinlemede: Türkçe karakterler (ş, ğ, ı, ö, ü, ç) doğru, kelime atlama/tekrar yok
**Son sonuç (14.10.2026):** ✅ üretim 76,8 sn, ses 16,76 sn, MPS driver 3,76 GB. Dinleme testi: ⏳ yapılmadı.

## TC-002 — CPU yedek yolu
**Adım:** `.venv/bin/python scripts/first_test_v3.py --device cpu --out outputs/first_test_v3_cpu.wav`
**Beklenen:** Çıkış kodu 0, WAV oluşur.
**Son sonuç:** Kısa cümleyle tanı amaçlı çalıştırıldı ✅ (45,7 sn); tam metinle ⏳ çalıştırılmadı.

## Negatif senaryolar
- **N-001** Watermark sınırı kaldırılırsa (`PYTORCH_MPS_HIGH_WATERMARK_RATIO=0`): üretim tamamlanır ama MPS ~16 GB'a çıkar, swap artar → kabul edilemez.
- **N-002** Yalnızca HIGH ayarlanıp LOW ayarlanmazsa: `RuntimeError: invalid low watermark ratio 1.4` → ikisi birlikte ayarlanmalı.
- **N-003** `language_id` desteklenmeyen dil kodu → `ValueError` beklenir. ⏳ test edilmedi.

---

# Web MVP (v0.1.0)

**Kurulum:** `scripts/run_studio.sh` → `http://127.0.0.1:8765`, sağ üstte "Hazır · MPS" görünene kadar bekle (~20 sn).
**Otomatik testler:** `.venv/bin/python -m unittest discover -s backend/tests -t .` (19 test, sahte motor) — ✅ 14.10.2026

| ID | Adımlar | Beklenen | Son sonuç |
|---|---|---|---|
| W-01 | 4 cümlelik hikâyeyi yaz → Seslendir | "4 parça"; "Parça n / 4" ilerlemesi; bitince oynatıcı otomatik çalar, geçmişe eklenir | ✅ 100,5 sn üretim, 19,16 sn ses |
| W-02 | Türkçe karakterli metin | ş ğ ı İ ö ü ç editörde/geçmişte bozulmaz | ✅ |
| W-03 | Oynatıcıdan WAV ve MP3 indir | `iesoft_YYYYMMDD_HHMM_xxxxxx.wav/.mp3`, MP3 24 kHz 160 kbps | ✅ |
| W-04 | Referans WAV yükle (izin kutusu işaretli) → seç → üret | Referans listede; klon sesle üretim | ✅ API ile (tarayıcı dosya seçici manuel test ⏳) |
| W-05 | Profil oluştur → başka ayara geç → profili seç | Ayarlar + referans geri gelir, "Klon ses" etiketi | ✅ |
| W-06 | Geçmişte "Metni ve ayarları yükle" | Metin, ayarlar, seed, referans geri yüklenir | ✅ |
| W-07 | Uzun üretimde İptal | "İptal ediliyor…" → mevcut parça bitince "İptal edildi"; geçmişe eklenmez | ✅ |
| W-08 | Sunucu yeniden başlat | Profiller ve geçmiş korunur | ✅ |
| W-09 | 375 px mobil görünüm | Tek sütun, panel çakışması yok, oynatıcı altta | ✅ |
| W-10 | Kulakla dinleme: telaffuz, doğallık, parça geçişleri | Klik/kesik yok, doğal duraklama | ⏳ Kullanıcı tarafından yapılmalı |

**Negatif senaryolar**
| ID | Durum | Beklenen | Son sonuç |
|---|---|---|---|
| WN-01 | Üretim sürerken ikinci Seslendir | Toast: "Şu anda başka bir seslendirme sürüyor…" (409) | ✅ |
| WN-02 | Boş metin / 5.000+ karakter | Buton pasif + açıklama; API 422 | ✅ |
| WN-03 | İzin onayı yok / <3 sn / >60 sn / sessiz / WAV olmayan dosya | Anlaşılır Türkçe hata, dosya kaydedilmez | ✅ (API testi) |
| WN-04 | Aynı isimde profil (büyük/küçük harf farkı) | 409 "… adında bir profil zaten var." | ✅ |
| WN-05 | Model yüklenirken üretim | Buton pasif "Model yükleniyor…"; API 503 | ✅ |
| WN-06 | Yabancı Origin'den POST / sahte Host | 403 / 400 | ✅ |
| WN-07 | Motor bellek hatası | "Bellek yetersiz…" mesajı | ✅ (sahte motor) |

## P-01 — Referanssız preset karşılaştırması
**Adım:** Sunucuyu durdur → `.venv/bin/python scripts/compare_presets.py`
**Beklenen:** "built-in voice (conds.pt) loaded: True"; `outputs/presets/` altında 3 WAV + `report.json`; `hit_token_limit` hepsi False.
**Son sonuç (14.10.2026):** ✅ otomatik ölçümler. Kulakla tekrar/eksik okuma kontrolü ⏳.

## P-02 — CFG aksan testi (varsayılan ses)
**Adım:** Web/API ile aynı metni cfg 0,0 / 0,2 / 0,5 (exag 0,5, temp 0,7, rep 1,2, seed 42) üret.
**Beklenen:** 3 parça, token sınırı yok, `outputs/cfg_test/` altında 3 WAV.
**Son sonuç (14.10.2026):** ✅ ölçümler; aksan değerlendirmesi kulakla ⏳.
**Negatif:** "IŞIK İnsan" → normalleştirici "ıŞıK insan" verir, tokenizer "ışık insan" okur. ✅ v0.2.0 ile düzeltildi (önceden "işik i̇nsan").

## v0.2.0 — Türkçe normalleştirme ve akıcı parçalama
**Otomatik:** 35 backend testi (`test_turkish_normalizer.py` 9, splitter 13, API 12 + 1) — ✅ 21.10.2026
| ID | Adım | Beklenen | Sonuç |
|---|---|---|---|
| T-01 | Editöre "Hz. Musa 3. gün… ABD'de %50… Saat 14:30'da IRMAK" yaz → "parça" listesini aç | "Hazreti Musa üçüncü gün… a be dede… yüzde elli… on dört otuzda ıRMAK" | ✅ |
| T-02 | "Yapay zekâ…" metnini üret | 6 parça; "Peki… neden?" aynı parçada; "kodla yazılmıyor…" sonrası uzun duraklama | ✅ ölçüm, kulak ⏳ |
| T-03 | A/B dinleme: `outputs/ab_test/once_cumle_cumle.wav` vs `sonra_normalize_gruplu.wav` | Sonrası daha akıcı, sayılar Türkçe, kelime atlaması yok | ⏳ kullanıcı |
| TN-01 | "Peki… neden" (üç nokta + küçük harf) | Cümle bölünmez | ✅ |
| TN-02 | `max_chars` < hedef | Parçalar `max_chars`'ı aşmaz (hata düzeltildi) | ✅ |
| TN-03 | "SEN", "IŞIK" gibi vurgu amaçlı büyük harf | Harf harf okunmaz, kelime olarak kalır | ✅ |
| T-04 | "ABD'de" için 3 yazım dinleme testi (`outputs/abd_test/`) | Kullanıcı en doğal olanı seçer | ✅ 21.10.2026: bitişik "abedede" seçildi |
