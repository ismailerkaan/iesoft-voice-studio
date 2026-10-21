# IESOFT Voice Studio — Mimari

Tamamen lokal çalışan Türkçe TTS stüdyosu. Tek süreç, tek port: `http://127.0.0.1:8765`.

```
Tarayıcı (React + Tailwind, frontend/dist)
   │  fetch /api/*  (1 sn aralıkla iş durumu sorgusu)
   ▼
FastAPI (backend/app/main.py)
   ├── JobManager (jobs.py)        tek slotlu üretim işçisi, iptal (parça arası)
   │      ├── turkish_normalizer.py sayı/%/tarih/saat/para/kısaltma → Türkçe kelime, I→ı / İ→i
   │      ├── text_splitter.py     cümle bölme + ~200 karakterlik gruplama, noktalamaya göre duraklama çarpanı
   │      ├── ChatterboxEngine     model bir kez yüklenir, bellekte kalır (tts_engine.py)
   │      └── audio.py             parça birleştirme + duraklama + tepe sınırlama, MP3 (ffmpeg)
   └── Storage (storage.py)        SQLite: reference_voices, profiles, generations
data/
   ├── studio.db
   ├── references/<uuid>.wav      yüklenen referanslar (mono PCM16'ya yeniden kodlanmış)
   └── generations/<uuid>.wav|mp3
```

## Kararlar
- **Model bellekte:** Uygulama açılışında arka plan iş parçacığında yüklenir (~20 sn). `/api/status` durumu verir.
- **Tek üretim:** İkinci istek `409` ile reddedilir (kuyruk yok — MVP).
- **Gerçek ilerleme:** Yalnızca tamamlanan parça sayısı gösterilir. Parça içinde model ölçülebilir ilerleme vermez; sahte yüzde yoktur.
- **Tekrarlanabilirlik:** Her iş başında `torch.manual_seed(seed)`; ayarlar + seed geçmişte saklanır.
- **Referans koşulları önbelleği:** Son 4 referansın conditioning'i bellekte tutulur.
- **MPS bellek sınırı:** `config.py` torch'tan önce `PYTORCH_MPS_HIGH/LOW_WATERMARK_RATIO=0.5/0.3` ayarlar (bkz. `docs/KAIDE.md`).
- **Geliştirme modu:** `cd frontend && npm run dev` → Vite `127.0.0.1:5173`, `/api` 8765'e proxy.
