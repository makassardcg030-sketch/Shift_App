"""Logika jadwal shift fleksibel (murni Python, tanpa Kivy/Android)."""
import csv
import datetime as dt
import re

HARI = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]

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

def _find_month(rows):
    for row in rows:
        for v in row:
            if isinstance(v, (dt.datetime, dt.date)):
                return v.year, v.month
            if isinstance(v, str):
                m = re.search(r"([A-Za-z]+)\.?\s*[-/ ]?\s*(\d{4})", v)
                if m and m.group(1).lower() in MONTHS:
                    return int(m.group(2)), MONTHS[m.group(1).lower()]
    raise ScheduleError("Judul bulan tidak ditemukan di baris atas file.")

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

def parse_code(v, off_words=("OFF", "LIBUR"), cuti_words=("C", "CUTI", "IZIN", "SAKIT")):
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
    if s in off_words:
        return "OFF"
    if s in cuti_words:
        return "C"
    m = re.fullmatch(r"(\d{1,2})(?:[:.]00)?", s)
    if m and int(m.group(1)) <= 23:
        return str(int(m.group(1)))
    return "X"

def parse_grid(rows, off_words=("OFF", "LIBUR"), cuti_words=("C", "CUTI", "IZIN", "SAKIT")):
    rows = [list(r) for r in rows]
    if not rows:
        raise ScheduleError("File kosong.")
    year, month = _find_month(rows[:6])

    hdr = name_col = None
    for ri, row in enumerate(rows[:10]):
        for ci, v in enumerate(row):
            if isinstance(v, str) and v.strip().lower() == "nama":
                hdr, name_col = ri, ci
                break
        if hdr is not None:
            break
    if hdr is None:
        raise ScheduleError("Kolom \"Nama\" tidak ditemukan.")

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
        raise ScheduleError("Baris tanggal (01..30) tidak ditemukan.")

    days = []
    for row in rows[day_row + 1:]:
        name = str(row[name_col] if name_col < len(row) else "").strip()
        if not name or name.lower() == "none":
            continue
        got = False
        for ci, d in day_cols.items():
            code = parse_code(row[ci] if ci < len(row) else None, off_words, cuti_words)
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
        raise ScheduleError("Tidak ada data jadwal terbaca.")
    return "%04d-%02d" % (year, month), days

def load_days(path, off_words=("OFF", "LIBUR"), cuti_words=("C", "CUTI", "IZIN", "SAKIT")):
    lower = path.lower()
    if lower.endswith(".csv"):
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(4096)
            f.seek(0)
            try:
                dialect = csv.Sniffer().sniff(sample, delimiters=",;\t")
            except csv.Error:
                dialect = csv.excel
            return parse_grid(list(csv.reader(f, dialect)), off_words, cuti_words)
    if lower.endswith(".xlsx"):
        from openpyxl import load_workbook
        wb = load_workbook(path, read_only=True, data_only=True)
        try:
            return parse_grid(list(wb.worksheets[0].iter_rows(values_only=True)), off_words, cuti_words)
        finally:
            wb.close()
    raise ScheduleError("Format file tidak didukung.")

def merge_days(old, month_key, new, today=None, keep_days=60):
    kept = [d for d in old if not d[0].startswith(month_key)]
    merged = kept + list(new)
    if today:
        limit = (today - dt.timedelta(days=keep_days)).isoformat()
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

def build_entries(days, dur_full=8, dur_short=5, exact_full_run=5):
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
            dur = dur_full
            if m.get(d + one) == "OFF":
                run, cur = 0, d
                while m.get(cur, "").isdigit():
                    run += 1
                    cur -= one
                bounded = cur in m
                if not (bounded and run == exact_full_run):
                    dur = dur_short
            entries.append({"date": d.isoformat(), "name": name,
                            "hour": int(code), "dur": dur, "_o": order[name]})
    entries.sort(key=lambda e: (e["date"], e["_o"]))
    for e in entries:
        del e["_o"]
    return entries

def entries_to_text(entries):
    return "\n".join("%s|%s|%d|%d" % (e["date"], e["name"], e["hour"], e["dur"])
                     for e in entries)

def _span(e):
    start = dt.datetime.fromisoformat(e["date"]) + dt.timedelta(hours=e["hour"])
    return start, start + dt.timedelta(hours=e["dur"])

def compute(entries, now):
    spans = [(_span(e), e) for e in entries]
    duty = [(e["name"], "%d+%d" % (e["hour"], e["dur"]))
            for (s, en), e in spans if s <= now < en]
    future = [s for (s, _), _e in spans if s > now]
    nxt = []
    if future:
        first = min(future)
        label = first.strftime("%H:%M") if first.date() == now.date() \
            else "%s %s" % (HARI[first.weekday()], first.strftime("%H:%M"))
        nxt = [(e["name"], label) for (s, _), _e in spans if s == first]
    return duty, nxt