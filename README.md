# Easy Media Downloader Library

Wrapper Python ergonomis dan ringan untuk mengunduh media (video, audio, atau gambar) dari **YouTube**, **TikTok**, **Instagram**, **Facebook**, dan **X (Twitter)**.

Bukan pengganti `yt-dlp`, melainkan lapisan pembungkus tipis (*thin wrapper*) untuk menyederhanakan pengambilan media tanpa kerumitan subtitle, playlist, thumbnail, atau dump metadata JSON.

---

## 🚀 Fitur Utama

- **API Simpel & Ergonomis**: `download(url)` auto-detect platform, plus alias per-platform (`download.youtube`, `download.tiktok`, `download.instagram`, `download.facebook`, `download.x` / `download.twitter`).
- **Format Return Seragam**:
  - Berhasil (single media): `{"type": "video"|"audio"|"image", "path": "...", "mimetype": "...", "bytes": BytesIO (opsional)}`
  - Berhasil (multi media / carousel / slide): List of dicts di atas.
  - Gagal / Melebihi limit: `{"error": "reason"}` atau `{"error": "reason", "exceeded_limit": True}` (Tanpa raise Exception).
- **Fleksibilitas Resolusi**: Resolusi berbasis angka `480`, `720`, `1080`, atau `"best"`, `"worst"`, `None`. Jika resolusi spesifik tidak tersedia, otomatis mengambil yang paling dekat tanpa throw error. Resolusi diabaikan untuk audio & gambar.
- **Short Links & Redirect Support**: Mendukung short links (`youtu.be`, `vt.tiktok.com`, `instagr.am`, `fb.watch`, `t.co`).
- **Batas Ukuran & Timeout**: Parameter `max_filesize` (bytes) & `timeout` (detik) yang configurable.
- **Dukungan Cookies**: `cookies_path` opsional untuk reel/post terproteksi.
- **Manajemen Temp & Cleanup**: Dilengkapi fungsi `cleanup()` untuk menghapus semua file/folder sementara hasil unduhan.

---

## 📦 Instalasi

Pastikan depedensi terinstal:
```bash
pip install -r requirements.txt
```

Atau instal `yt-dlp` & `requests` secara langsung:
```bash
pip install yt-dlp requests
```

---

## 📖 Contoh Penggunaan

### 1. Download Auto-Detect Platform
```python
from downloader import download, cleanup

# Video YouTube
res = download("https://youtu.be/dQw4w9WgXcQ", resolution=720)
print(res)
# Output: {'type': 'video', 'path': '/tmp/media_dl_.../dQw4w9WgXcQ.mp4', 'mimetype': 'video/mp4'}

# Hapus file temp setelah selesai digunakan
cleanup()
```

### 2. Fungsi Per-Platform
```python
from downloader import download

# YouTube Video / Audio
res_yt = download.youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ", media_type="audio")

# TikTok Video / Slide
res_tt = download.tiktok("https://www.tiktok.com/@user/video/1234567890")

# Instagram Reel / Carousel
res_ig = download.instagram("https://www.instagram.com/p/C123456/", cookies_path="cookies.txt")

# Facebook Video
res_fb = download.facebook("https://fb.watch/123456/")

# X / Twitter Video & Multi-photo
res_x = download.x("https://x.com/user/status/1234567890")
```

### 3. Mengambil Media Sebagai Bytes (BytesIO)
```python
res = download("https://youtu.be/dQw4w9WgXcQ", as_bytes=True)
if "error" not in res:
    bytes_data = res["bytes"] # io.BytesIO
```

### 4. Penanganan Batas Ukuran & Error
```python
# Set limit 10 MB (10 * 1024 * 1024 bytes)
res = download("https://youtu.be/dQw4w9WgXcQ", max_filesize=10485760)

if "error" in res:
    if res.get("exceeded_limit"):
        print("File terlalu besar:", res["error"])
    else:
        print("Gagal mengunduh:", res["error"])
```

---

## ⚙️ Catatan Arsitektur & Extractor Engine

- **YouTube**: Menggunakan engine `yt-dlp`.
- **Facebook**: Menggunakan engine `yt-dlp`.
- **TikTok**: Utama menggunakan `yt-dlp` untuk video. Jika link berupa TikTok Image Slide (foto carousel), otomatis fallback ke *custom light extractor* berbasis parse JSON page data.
- **Instagram**: Utama menggunakan `yt-dlp` untuk Reel/Video. Jika link berupa photo carousel, otomatis fallback ke *custom light extractor* (metatag/JSON parsing).
- **X (Twitter)**: Utama menggunakan `yt-dlp` untuk Tweet berisi video. Jika link berupa Tweet multi-photo / gambar, otomatis fallback ke Twitter syndication API & metatag extractor.
