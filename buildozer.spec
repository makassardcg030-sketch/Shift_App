[app]

# (str) Judul aplikasi Anda
title = Jadwal Shift App

# (str) Nama package (Pastikan BERBEDA dengan aplikasi restart sebelumnya agar tidak bentrok)
package.name = shiftapp

# (str) Domain package (unik untuk identifikasi di Android)
package.domain = org.shiftapp

# (list) Berkas sumber yang disertakan (pisahkan dengan spasi)
source.include_exts = py,png,jpg,kv,atlas,xlsx,csv

# (list) Direktori sumber (relatif terhadap direktori spec)
source.include_dirs = 

# (list) Berkas yang dikecualikan dari source
source.exclude_exts = spec

# (list) Daftar direktori yang dikecualikan
source.exclude_dirs = tests bin venv

# (list) Ekstensi file yang dikecualikan (opsional)
#source.exclude_patterns = license,images/*/*.jpg

# (str) Versi aplikasi
version = 1.0

# (list) Ketergantungan aplikasi (Penting: Sertakan python3, kivy, pandas, openpyxl untuk Excel/CSV)
requirements = python3,kivy,pandas,openpyxl,xlrd

# (str) Perintah orientasi layar (portrait, landscape, atau all)
orientation = portrait

# (bool) Indikator apakah aplikasi fullscreen atau tidak
fullscreen = 0

# (list) Izin aplikasi (android.permissions)
# Izin untuk membaca penyimpanan eksternal agar bisa memilih file excel/csv dari memori HP
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (str) Versi minimum SDK Android yang didukung
android.minapi = 21

# (str) Versi target SDK Android
android.sdk = 31

# (str) Arsitektur target build (armeabi-v7a, arm64-v8a)
android.archs = arm64-v8a, armeabi-v7a

# (bool) Gunakan androidx untuk pustaka Android modern
android.androidx = True


[buildozer]

# (int) Level log (0 = error saja, 1 = info, 2 = debug dengan detail)
log_level = 2

# (int) Menampilkan peringatan (0 = matikan, 1 = aktifkan)
warn_on_root = 1

# (str) Direktori penampung hasil build (default: ./bin)
bin_dir = ./bin