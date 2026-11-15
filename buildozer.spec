[app]

# (str) Judul aplikasi
title = Jadwal Shift App

# (str) Nama package -> package lengkap: org.shiftapp.shiftapp
# (HARUS sama dengan "package" di file Java: java_src/org/shiftapp/shiftapp/)
package.name = shiftapp
package.domain = org.shiftapp

source.dir = .
source.include_exts = py,png,jpg,kv,atlas
# Pemisah HARUS koma (sebelumnya spasi, sehingga tidak berfungsi)
source.exclude_dirs = tests, tools, bin, venv, java_src, widget_res, .github, .git

version = 1.2

# pandas DIHAPUS: terlalu berat dikompilasi di Android (butuh numpy 2 + meson)
# dan sering membuat build gagal. Excel dibaca dengan openpyxl, CSV dengan modul csv.
requirements = python3,kivy,pyjnius,openpyxl,et_xmlfile

orientation = portrait
fullscreen = 0

# Tidak perlu izin storage: file dipilih lewat pemilih file bawaan Android (SAF).

# ---- Android ----
android.api = 33
android.minapi = 24
android.archs = arm64-v8a, armeabi-v7a

# Wajib untuk build non-interaktif (CI), kalau tidak build berhenti menunggu input.
android.accept_sdk_license = True

# ---- Widget homescreen ----
# Kode Java widget + resource layout-nya
android.add_src = java_src
android.add_resources = widget_res/layout:layout, widget_res/xml:xml, widget_res/drawable:drawable

# python-for-android TIDAK diatur di sini. Workflow (.github/workflows/build.yml)
# meng-clone python-for-android versi tag v2024.01.21, menyisipkan <receiver> widget
# ke template AndroidManifest (tools/patch_p4a.py + widget_res/receiver.xml), lalu
# menambahkan baris "p4a.source_dir" ke file ini. Jadi p4a.branch / p4a.commit /
# p4a.extra_args sengaja tidak dipakai (commit lama tidak ada di repo, dan opsi
# --extra-manifest-application-xml tidak ada di python-for-android).


[buildozer]

log_level = 2
warn_on_root = 1
bin_dir = ./bin
