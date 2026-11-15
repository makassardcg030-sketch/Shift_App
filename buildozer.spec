[app]

# (str) Judul aplikasi Anda
title = Jadwal Shift App

# (str) Nama package 
package.name = shiftapp

# (str) Domain package
package.domain = org.shiftapp

# (str) Source directory where the application lives
source.dir = .

# (list) Berkas sumber yang disertakan
source.include_exts = py,png,jpg,kv,atlas,xlsx,csv

# (list) Berkas yang dikecualikan dari source
source.exclude_exts = spec

# (list) Daftar direktori yang dikecualikan
source.exclude_dirs = tests bin venv

# (str) Versi aplikasi
version = 1.0

# (list) Ketergantungan aplikasi
requirements = python3,kivy,pandas,openpyxl,xlrd

# (str) Perintah orientasi layar
orientation = portrait

# (bool) Indikator apakah aplikasi fullscreen atau tidak
fullscreen = 0

# (list) Izin aplikasi
android.permissions = READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE

# (str) Versi minimum SDK Android yang didukung
android.minapi = 21

# (str) Versi target SDK Android
android.sdk = 31

# (str) Arsitektur target build
android.archs = arm64-v8a, armeabi-v7a

# (bool) Gunakan androidx untuk pustaka Android modern
android.androidx = True


[buildozer]

# (int) Level log
log_level = 2

# (int) Menampilkan peringatan
warn_on_root = 1

# (str) Direktori penampung hasil build
bin_dir = ./bin
