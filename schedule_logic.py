"""Logika jadwal shift (murni Python, tanpa Kivy/Android) supaya mudah diuji.

FORMAT FILE (xlsx, atau csv dengan tata letak yang sama)
--------------------------------------------------------
  - Judul bulan di baris atas, mis. "November 2026" (teks atau sel tanggal).
  - Header: kolom "NIK" dan "Nama", lalu satu kolom per tanggal.
    Baris nama hari (MIN SEN ...) boleh ada; baris angka tanggal (01..30) wajib.
  - Satu baris per orang. Isi sel:
        angka (6, 8, 11, 14, 22)  -> jam MULAI shift
        off                       -> libur
        C                         -> cuti
        kosong / teks lain        -> tidak bertugas

ATURAN DURASI
-------------
  - Normal: mulai + 8 jam   (14 -> 14:00-22:00, 22 -> 22:00-06:00 besok).
  - Hari terakhir sebelum "off": mulai + 5 jam.
  - Pengecualian: jika hanya ada 5 hari kerja di antara dua hari libur
    (off/C), hari terakhir itu tetap +8.
  - Rangkaian kerja yang terpotong awal bulan (hari sebelum tanggal 1 tidak
    diketahui) dianggap tidak bisa dipastikan 5 hari -> tetap +5.
    Begitu file bulan sebelumnya juga pernah diunggah, aturan dihitung benar.
"""
import csv
import datetime as dt
import re

HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

DUR_FULL = 8        # durasi normal (jam)
DUR_SHORT = 5       # durasi hari terakhir sebelum off (jam)
EXACT_FULL_RUN = 5  # jika rangkaian kerja persis segini hari -> tetap DUR_FULL
KEEP_DAYS = 60      # data lebih tua dari ini dibuang

OFF_WORDS = ("OFF", "LIBUR")
CUTI_WORDS = ("C", "CUTI")

MONTHS = {
    "januari": 1, "january": 1, "jan": 1,
    "februari": 2, "february": 2, "feb": 2, "pebruari": 2,
    "maret": 3, "march": 3, "mar": 3,
    "april": 4, "apr": 4,
    "mei": 5, "may": 5,
    "juni": 6, "june": 6, "jun": 6,
    "juli": 7, "july": 7, "jul": 7,
    "agustus": 8, "august": 8, "agu": 8, "agt": 8, "aug": 8,
    "september": 9, "sep": 9, "sept": 9,
    "oktober": 10, "october": 10, "okt": 10, "oct": 10,
    "november": 11, "nopember": 11, "nov": 11,
    "desember": 12, "december": 12, "des": 12, "dec": 12,
}


class ScheduleError(Exception):
    pass


# ---------------------------------------------------------------- membaca file
def _find_month(rows):
    """Cari (tahun, bulan) dari judul di beberapa baris teratas."""
    for row in rows:
        for v in row:
            if isinstance(v, (dt.datetime, dt.date)):
                return v.year, v.month
            if isinstance(v, str):
                m = re.search(r"([A-Za-z]+)\.?\s*[-/ ]?\s*(\d{4})", v)
                if m and m.group(1).lower() in MONTHS:
                    return int(m.group(2)), MONTHS[m.group(1).lower()]
    raise ScheduleError(
        "Judul bulan tidak ditemukan. Tulis di baris atas file, mis. \"November 2026\".")


def _day_number(v):
    if isinstance(v, (dt.datetime, dt.date)):
        return v.day
    try:
        f = float(str(v).strip())
    except (TypeError, ValueError):
        return None
    if f.is_integer() and 1 <= int(f) <= 31:
        return int(f)
    return None


def parse_code(v):
    """Sel jadwal -> '14' (jam mulai) | 'OFF' | 'C' | 'X' (lainnya) | None (kosong)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, dt.datetime):
        v = v.time()
    if isinstance(v, dt.time):
        return str(v.hour)
    if isinstance(v, (int, float)):
        if float(v).is_integer() and 0 <= int(v) <= 23:
            return str(int(v))
        return "X"
    s = str(v).strip().upper()
    if not s:
        return None
    if s in OFF_WORDS:
        return "OFF"
    if s in CUTI_WORDS:
        return "C"
    m = re.fullmatch(r"(\d{1,2})(?:[:.]00)?", s)
    if m and int(m.group(1)) <= 23:
        return str(int(m.group(1)))
    return "X"


def parse_grid(rows):
    """Baris-baris sel -> (kunci_bulan 'YYYY-MM', [(tanggal_iso, nama, kode), ...])."""
    rows = [list(r) for r in rows]
    if not rows:
        raise ScheduleError("File kosong.")
    year, month = _find_month(rows[:6])

    # posisi header "Nama"
    hdr = name_col = None
    for ri, row in enumerate(rows[:10]):
        for ci, v in enumerate(row):
            if isinstance(v, str) and v.strip().lower() == "nama":
                hdr, name_col = ri, ci
                break
        if hdr is not None:
            break
    if hdr is None:
        raise ScheduleError("Kolom \"Nama\" tidak ditemukan di header.")

    # baris angka tanggal (01..30)
    day_row, day_cols = None, {}
    for ri in range(hdr, min(hdr + 4, len(rows))):
        cols = {}
        for ci in range(name_col + 1, len(rows[ri])):
            d = _day_number(rows[ri][ci])
            if d is not None:
                cols[ci] = d
        if len(cols) >= 28:
            day_row, day_cols = ri, cols
            break
    if day_row is None:
        raise ScheduleError("Baris tanggal (01, 02, ... 30) tidak ditemukan di bawah header.")

    days = []
    for row in rows[day_row + 1:]:
        name = str(row[name_col] if name_col < len(row) else "").strip()
        if not name or name.lower() == "none":
            continue
        got = False
        for ci, d in day_cols.items():
            code = parse_code(row[ci] if ci < len(row) else None)
            if code is None:
                continue
            try:
                date = dt.date(year, month, d)
            except ValueError:
                continue
            days.append((date.isoformat(), name, code))
            got = True
        if not got:
            continue
    if not days:
        raise ScheduleError("Tidak ada data jadwal yang terbaca di file.")
    return "%04d-%02d" % (year, month), days


def _sniff_kind(path):
    """Tentukan 'xlsx' / 'csv' dari ekstensi, atau dari isi file bila ekstensi hilang
    (Google Drive / WhatsApp / Downloads kadang memberi nama tanpa .xlsx)."""
    lower = path.lower()
    if lower.endswith(".xlsx") or lower.endswith(".xlsm"):
        return "xlsx"
    if lower.endswith(".csv"):
        return "csv"
    with open(path, "rb") as f:
        head = f.read(4)
    if head[:2] == b"PK":
        return "xlsx"
    if head[:4] == b"\xd0\xcf\x11\xe0":
        raise ScheduleError("File .xls (format lama) tidak didukung. Simpan ulang sebagai .xlsx.")
    return "csv"


def load_days(path):
    kind = _sniff_kind(path)
    if kind == "csv":
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except csv.Error:
                dialect = csv.excel
            return parse_grid(list(csv.reader(f, dialect)))
    from openpyxl import load_workbook
    # read_only=False: lebih toleran terhadap xlsx hasil ekspor Google Sheets/Mac
    # (dimensi sheet / drawing yang tidak standar).
    # Dibuka lewat objek file: openpyxl menolak path yang tidak berakhiran .xlsx.
    with open(path, "rb") as fh:
        wb = load_workbook(fh, data_only=True)
        try:
            return parse_grid(list(wb.worksheets[0].iter_rows(values_only=True)))
        finally:
            wb.close()


# ------------------------------------------------------- penyimpanan & gabungan
def merge_days(old, month_key, new, today=None):
    """Ganti data bulan month_key dengan file baru, bulan lain dipertahankan."""
    kept = [d for d in old if not d[0].startswith(month_key)]
    merged = kept + list(new)
    if today:
        limit = (today - dt.timedelta(days=KEEP_DAYS)).isoformat()
        merged = [d for d in merged if d[0] >= limit]
    return merged


def days_to_text(days):
    return "\n".join("|".join(d) for d in days)


def text_to_days(text):
    out = []
    for line in (text or "").splitlines():
        p = line.strip().split("|")
        if len(p) == 3:
            out.append((p[0], p[1], p[2]))
    return out


# --------------------------------------------------------------- hitung durasi
def build_entries(days):
    """[(tanggal, nama, kode)] -> [{'date','name','hour','dur'}] dengan aturan +8/+5."""
    order = {}
    by_name = {}
    for date_iso, name, code in days:
        order.setdefault(name, len(order))
        by_name.setdefault(name, {})[dt.date.fromisoformat(date_iso)] = code

    one = dt.timedelta(days=1)
    entries = []
    for name, m in by_name.items():
        for d, code in m.items():
            if not code.isdigit():
                continue
            dur = DUR_FULL
            if m.get(d + one) == "OFF":
                run, cur = 0, d
                while m.get(cur, "").isdigit():
                    run += 1
                    cur -= one
                bounded = cur in m  # hari sebelum rangkaian diketahui (off/C/lainnya)
                if not (bounded and run == EXACT_FULL_RUN):
                    dur = DUR_SHORT
            entries.append({"date": d.isoformat(), "name": name,
                            "hour": int(code), "dur": dur, "_o": order[name]})
    entries.sort(key=lambda e: (e["date"], e["_o"]))
    for e in entries:
        del e["_o"]
    return entries


def entries_to_text(entries):
    """Format untuk widget Java: yyyy-MM-dd|Nama|jam|durasi"""
    return "\n".join("%s|%s|%d|%d" % (e["date"], e["name"], e["hour"], e["dur"])
                     for e in entries)


# ------------------------------------------------------------ duty / next
def _span(e):
    start = dt.datetime.fromisoformat(e["date"]) + dt.timedelta(hours=e["hour"])
    return start, start + dt.timedelta(hours=e["dur"])


def compute(entries, now):
    """Return (duty, next):
         duty = [(nama, '14+8'), ...]
         next = [(nama, '22:00' atau 'Sen 06:00'), ...]
    Aturan sama dengan ShiftWidgetProvider.java."""
    spans = [(_span(e), e) for e in entries]
    duty = [(e["name"], "%d+%d" % (e["hour"], e["dur"]))
            for (s, en), e in spans if s <= now < en]
    future = [s for (s, _), _e in spans if s > now]
    nxt = []
    if future:
        first = min(future)
        label = first.strftime("%H:%M") if first.date() == now.date() \
            else "%s %s" % (HARI[first.weekday()], first.strftime("%H:%M"))
        nxt = [(e["name"], label) for (s, _), e in spans if s == first]
    return duty, nxt
