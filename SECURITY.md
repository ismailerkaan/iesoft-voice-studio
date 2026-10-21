# Güvenlik Notları

| # | Risk | Önlem | Durum |
|---|---|---|---|
| S1 | Ağdan erişim | Uvicorn yalnızca `127.0.0.1`'e bağlanır | ✅ |
| S2 | DNS rebinding | `TrustedHostMiddleware` (yalnızca `127.0.0.1`, `localhost`) | ✅ test edildi |
| S3 | CSRF (başka sitenin lokal API'ye form/POST göndermesi) | Yabancı `Origin` başlıklı yazma istekleri 403 | ✅ test edildi |
| S4 | Path traversal | Dosya yolları yalnızca sunucu üretimi UUID'lerden kurulur; ID'ler doğrulanır | ✅ test edildi |
| S5 | Kötü amaçlı/bozuk ses dosyası | Boyut sınırı, WAV formatı ve süre kontrolü, mono PCM16'ya yeniden kodlama | ✅ test edildi |
| S6 | Komut enjeksiyonu (ffmpeg) | `subprocess.run` liste argümanlarıyla, kabuk yok | ✅ |
| S7 | XSS | React otomatik kaçışlama; `dangerouslySetInnerHTML` yok | ✅ |
| S8 | İzinsiz ses klonlama | Yüklemede izin onayı zorunlu (sunucu tarafında da kontrol) | ✅ |
| S9 | Kimlik doğrulama yok | Tek kullanıcılı lokal uygulama; ağa açılmamalı | ⚠️ Bilinçli kabul |
| S10 | Frontend bağımlılıkları | Sürümler sabit, `npm audit` 0 açık (14.10.2026) | ✅ |
