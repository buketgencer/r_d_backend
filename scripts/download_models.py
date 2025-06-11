# Tek seferlik yardımcılar
# HuggingFace/transformers modellerini
# offline sunucuya indirmek için

#(Opsiyonel) İnternetsiz sunucuya modelleri önceden indirme kolaylığı

from huggingface_hub import snapshot_download

snapshot_download(
    repo_id="sentence-transformers/all-MiniLM-L6-v2",
    local_dir="models/all-MiniLM-L6-v2",
    local_dir_use_symlinks=False, # neden False? Çünkü bu, dosyaları gerçek kopyalar olarak indirir, sembolik bağlantılar oluşturmaz. Bu, bazı sistemlerde sorunlara neden olabilir ve tüm dosyaların fiziksel olarak mevcut olmasını sağlar.
)

# yukarıda kod çalışma şekli # - `snapshot_download` fonksiyonu, belirtilen modelin tüm dosyalarını indirir.