# jalankan.py - Aman untuk di-push ke GitHub
# Cara pakai: python jalankan.py
# File ini TIDAK berisi path laptop, password, atau data pribadi.
# Jadi aman kalau di-clone di laptop lain.

import subprocess
import sys
import re
from pathlib import Path

# Cari folder tempat file ini berada, bukan D:\... manual
# Jadi kalau di-clone di laptop lain, tetap ketemu main.py
FOLDER_PROJECT = Path(__file__).parent
FILE_UTAMA = FOLDER_PROJECT / "main.py"

print("=== MENJALANKAN Shift_App ===")
print(f"File: {FILE_UTAMA.name}") # Cuma tampilkan namanya aja, bukan path lengkapnya

if not FILE_UTAMA.exists():
    print("❌ File main.py tidak ditemukan di folder ini.")
    print("Pastikan jalankan.py dan main.py ada di folder yang sama.")
    sys.exit(1)

hasil = subprocess.run([sys.executable, str(FILE_UTAMA)], capture_output=True, text=True, cwd=FOLDER_PROJECT)

if hasil.stdout:
    print(hasil.stdout)

if "ModuleNotFoundError" in hasil.stderr:
    cari = re.search(r"No module named '([^']+)'", hasil.stderr)
    if cari:
        modul_hilang = cari.group(1)
        # Nama import kadang beda dengan nama install
        ganti_nama = {
            "PIL": "pillow",
            "cv2": "opencv-python",
            "sklearn": "scikit-learn",
        }
        nama_install = ganti_nama.get(modul_hilang, modul_hilang)

        print("\n" + "="*50)
        print(f"❌ MODUL BELUM TERINSTALL: {modul_hilang}")
        print("="*50)
        print("COPY PERINTAH DI BAWAH INI:")
        print()
        print(f"python -m pip install {nama_install}")
        print()
        print("="*50)
        tanya = input("Mau langsung saya install-in sekarang? (y/n): ").lower()
        if tanya == "y":
            print(f"Menginstall {nama_install}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", nama_install])
            print("✅ Berhasil! Jalankan lagi: python jalankan.py")
    else:
        print(hasil.stderr)
elif hasil.stderr:
    print(hasil.stderr)
else:
    print("✅ Berjalan tanpa error.")