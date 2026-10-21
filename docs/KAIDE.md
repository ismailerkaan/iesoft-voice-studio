# Kalıcı Kurallar

1. Chatterbox `5de7a54` commit'ine sabittir; `.venv` paketleri izinsiz güncellenmez. Kurulu paketler: `requirements.lock.txt`.
2. MPS'te `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5` ve `PYTORCH_MPS_LOW_WATERMARK_RATIO=0.3` **birlikte** ayarlanır (yalnızca biri → RuntimeError; hiçbiri → ~16 GB MPS önbelleği ve swap).
3. Model her istekte yeniden yüklenmez; aynı anda yalnızca bir üretim çalışır.
4. Ölçülemeyen ilerleme için yüzde gösterilmez.
5. Referans ses yalnızca kullanıcı kullanım/klonlama iznini onayladığında kabul edilir.
6. Sunucu yalnızca `127.0.0.1`'e bağlanır; Host doğrulaması ve yabancı Origin'den yazma engeli kaldırılmaz.
7. Model desteklemediği özellik (ör. doğrudan hız parametresi) varmış gibi gösterilmez.
