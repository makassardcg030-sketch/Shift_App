# Perbaikan Shift_App (8 permintaan)

1. **Tema tidak berubah** — Penyebab: `change_theme()` lama hanya ubah 4 variabel global, tapi `RoundedCard`/`ModernButton` sudah mengunci warna di canvas saat `__init__`. Perbaikan: palet lengkap per tema + `set_bg()` + apply ke SEMUA kartu/tombol yang sudah ada + simpan ke `settings.json` + tambah tema Terang. Widget Android tetap hardcoded — tema widget perlu `SharedPreferences` + `RemoteViews.setInt()` terpisah (lihat Saran).
2. **Widget lebih menarik** — `shift_widget.xml` & `personal_widget.xml` didesain ulang: header gelap + aksen kuning, radius 16dp, border, label Indonesia, kontras lebih baik. `widget_bg.xml` dari hitam pekat + radius 4dp -> slate + radius 16dp + stroke.
3. **Tampilan utama** — Struktur sama (agar tidak merusak), tapi: tombol Pengaturan Shift baru, status lebih jelas, palet konsisten lewat tema. Saran desain lanjutan ada di bawah.
4. **Jadwal dinamis** — Baru: `Pengaturan Shift` popup. Format `P=6,8` / `S=14,8` / `M=22,8` / `C=LIBUR` / `OFF=LIBUR`, tersimpan di `settings.json`. `schedule_logic.build_entries(..., shift_defs=...)` memetakan kode huruf ke (jam,durasi). Excel angka lama tetap jalan (fallback).
5. **Alarm berhasil** — Di aplikasi: sekarang muncul POPUP "Alarm Berhasil Disetel" + status ✓, bukan cuma teks kecil. Di widget personal: Toast sudah ada, diperjelas jadi "✓ Alarm berhasil disetel pukul ...".
6. **Urutan Duty by jam** — `schedule_logic.build_entries` sort by `(date, hour)`, `compute()` sort duty by hour, `ShiftWidgetProvider.compute()` sort entries by `start` sebelum ditampilkan. Sebelumnya sort by `(date, urutan_nama_di_Excel)`.
7. **Bahasa Indonesia** — `Name->Nama`, `Time->Jam`, `Duty:->Bertugas:`, `Next:->Berikutnya:`, `Duty: -` dll. Sisa yang masih Inggris di kode: cek `PERBAIKAN.md` bagian Sisa Inggris.
8. **Saran & file yang belum dilampirkan** — lihat bawah.

## Sisa teks Inggris (sengaja tidak diubah karena teknis)
- `buildozer.spec`, nama package, log, nama file `template_jadwal_shift.xlsx` — jangan diubah.
- `HARI` sudah Indonesia.

## Saran menarik (belum dikerjakan, perlu keputusanmu)
- **Tema widget ikut tema aplikasi**: butuh kirim `theme` dari Python ke `SharedPreferences` + widget baca tema itu. Mau dibuatkan?
- **Notifikasi H-1 jam otomatis** tanpa tekan tombol (WorkManager/AlarmManager di widget) — saat ini alarm hanya saat tombol ditekan.
- **Riwayat & rekap**: total jam kerja per orang per bulan, hitung lembur.
- **Mode gelap widget personal**: saat ini header putih di file lama, sudah diubah ke gelap.
- **Backup jadwal ke Google Drive / export CSV**.

## File yang belum kamu lampirkan (penting untuk analisa penuh)
- `AndroidManifest.xml` (digenerate Buildozer, tapi kalau kamu custom, lampirkan) — perlu cek permission `SET_ALARM`, `SCHEDULE_EXACT_ALARM`, `POST_NOTIFICATIONS`.
- Screenshot tampilan di HP (widget di homescreen + aplikasi) — untuk nilai desain secara visual.
- File `buildozer.spec` sudah ada, tapi log build terakhir (`build.log`) kalau pernah gagal build.
- Versi `main.py` di branch `tambah-sample` (ada di .git) — belum dicek apakah lebih baru dari `main`.
- File Excel asli (bukan `contoh_jadwal.xlsx`) kalau formatnya beda dari contoh.
