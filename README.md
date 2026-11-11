# hermes-android-wheels

Membangun wheel Python 3.14 untuk Android (`android_24_arm64_v8a` dan `android_24_x86_64`) bagi dependensi native **hermes-agent v0.23.1** yang tidak tersedia di PyPI. Dipakai oleh proyek Hermes Native Android sebagai `wheelhouse/` (gerbang G1).

Tidak ada kode Hermes di repo ini. Sumber setiap paket diunduh saat build dari PyPI (sdist) atau GitHub (psutil), pada versi dan hash yang tercatat di `uv.lock` upstream — lihat `packages.json`.

## Isi

| Berkas | Fungsi |
|---|---|
| `packages.json` | daftar paket, versi, URL sdist, sha256, tier |
| `scripts/fetch_source.py` | unduh + verifikasi sha256 + ekstrak aman |
| `scripts/fetch_deps.py` | unduh libffi/OpenSSL Android dari `beeware/cpython-android-source-deps` (hanya job tier 3) |
| `scripts/matrix.py` | matriks job (paket × ABI) |
| `.github/workflows/android-wheels.yml` | build dengan `cibuildwheel --platform android` di `ubuntu-24.04` |

## Paket

| Tier | Paket | Catatan |
|---|---|---|
| 1 — wajib | `pydantic-core 2.50.1`, `jiter 0.17.0`, `psutil` @ `380bd2b5` | terukur dimuat saat satu giliran `AIAgent`; job `collect` gagal bila ada yang hilang |
| 2 | `watchfiles 1.3.0`, `httptools 0.8.0` | dependensi inti, tidak dimuat di jalur agen |
| 3 — eksperimental | `cffi 2.1.1`, `cryptography 50.0.2`, `pillow 13.0.0` | butuh libffi / OpenSSL / tanpa JPEG; `continue-on-error`, mungkin perlu perbaikan setelah run pertama |
| tidak dibangun | `pillow-heif`, `firecrawl-anydoc` | lihat `packages.json` |

## Cara menjalankan

1. Buat repo kosong di GitHub (privat atau publik), misalnya `hermes-android-wheels`. Jangan centang "Add a README".
2. Dari folder ini:

   ```bash
   git remote add origin https://github.com/<akun-anda>/hermes-android-wheels.git
   ```

   ```bash
   git push -u origin main
   ```

3. Buka tab **Actions** di repo. Workflow `android-wheels` berjalan otomatis setelah push (atau jalankan manual lewat **Run workflow**). 16 job; perkiraan 10–25 menit.
4. Setelah selesai, buka run tersebut → bagian **Artifacts** → unduh `wheelhouse` (zip).
5. Simpan zip itu sebagai `hermes_native_android/project/wheelhouse.zip`.

Ringkasan run (tabel paket × ABI) tampil di halaman run. Bila job tier 1 gagal, salin log job yang gagal.

## Status

Workflow ini **belum pernah dijalankan** — ditulis dari dokumentasi cibuildwheel 4.3 (dukungan Android, termasuk Rust sejak 3.4). Job tier 1 dan 2 memakai jalur standar; job tier 3 memakai asumsi tentang cara `CFLAGS`/`LDFLAGS`/`OPENSSL_DIR` diteruskan ke lingkungan build silang dan paling mungkin perlu penyesuaian.

## Keamanan rantai pasok

- Action GitHub di-pin ke commit SHA.
- sdist diverifikasi sha256 dari `uv.lock` upstream sebelum diekstrak.
- `permissions: contents: read`; tidak ada secret yang dipakai.
- Keluaran: `wheelhouse/*.whl`, `SHA256SUMS`, `build-report.json`.
