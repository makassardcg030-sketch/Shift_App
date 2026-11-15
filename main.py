import os

from kivy.app import App
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.utils import platform
from datetime import date, datetime

import schedule_logic as sl

PICK_REQUEST = 4711
PKG = "org.shiftapp.shiftapp"


WHITE, BLACK = (1, 1, 1, 1), (0, 0, 0, 1)
RED, BLUE, YELLOW = (1, 0, 0, 1), (0, 0.44, 0.75, 1), (1, 1, 0, 1)
COL_WEIGHTS = (1.0, 1.6, 1.1, 1.6, 1.1)  # sama dengan layout widget


class Cell(Label):
    """Label dengan warna latar (meniru sel tabel di widget)."""

    def __init__(self, text="", bg=WHITE, fg=BLACK, bold=False, **kwargs):
        super().__init__(text=text, color=fg, bold=bold, shorten=True,
                         shorten_from="right", **kwargs)
        with self.canvas.before:
            Color(*bg)
            self._rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)
        self.bind(size=lambda *_: setattr(self, "text_size", self.size))
        self.halign = "center"
        self.valign = "middle"

    def _sync(self, *_):
        self._rect.pos = self.pos
        self._rect.size = self.size


class ShiftApp(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = 20
        self.spacing = 15
        self.entries = []
        self.days = []

        self.add_widget(Label(text="[b]Aplikasi Jadwal Shift & Widget[/b]", markup=True,
                              font_size=22, size_hint_y=None, height=40))

        self.btn_upload = Button(text="Upload File Jadwal (Excel/CSV)",
                                 size_hint_y=None, height=50)
        self.btn_upload.bind(on_press=self.open_picker)
        self.add_widget(self.btn_upload)

        self.lbl_status = Label(text="Belum ada file yang diunggah.",
                                size_hint_y=None, height=30)
        self.add_widget(self.lbl_status)

        # Pratinjau widget: HARI INI / header / Duty / Next
        self.table = BoxLayout(orientation="vertical", size_hint_y=None, height=170, spacing=2)
        top = BoxLayout(spacing=2)
        self.lbl_today = Cell("", WHITE, RED, bold=True, size_hint_x=1.0)
        self.lbl_clock = Cell("", WHITE, RED, bold=True, size_hint_x=1.0)
        top.add_widget(Cell("HARI INI", WHITE, BLACK, bold=True, size_hint_x=0.8))
        top.add_widget(self.lbl_today)
        top.add_widget(Cell("Time", WHITE, BLACK, bold=True, size_hint_x=0.6))
        top.add_widget(self.lbl_clock)
        self.table.add_widget(top)
        self.table.add_widget(self._row(("SHIFT", "Name", "Time", "Name", "Time"), RED, WHITE, True))
        self.duty_cells = self._row(("Duty:", "-", "", "", ""), BLUE, WHITE)
        self.next_cells = self._row(("Next:", "-", "", "", ""), YELLOW, BLACK)
        self.table.add_widget(self.duty_cells)
        self.table.add_widget(self.next_cells)
        self.add_widget(self.table)

        self.add_widget(Label(
            text="Pasang widget: tahan lama layar utama > Widget > \"Jadwal Shift\".\n"
                 "File: Excel (.xlsx) dengan judul bulan, kolom NIK, Nama, lalu tanggal 01-31.\n"
                 "Isi sel: jam mulai (6/8/11/14/22), off, atau C.",
            halign="center", font_size=14))

    def _row(self, texts, bg, fg, bold=False):
        row = BoxLayout(spacing=2)
        for t, w in zip(texts, COL_WEIGHTS):
            row.add_widget(Cell(t, bg, fg, bold=bold, size_hint_x=w))
        return row

    # ---------- memilih file ----------
    def open_picker(self, *_):
        if platform == "android":
            self._open_android_picker()
        else:  # untuk uji coba di PC
            content = FileChooserListView(filters=["*.xlsx", "*.csv"])
            content.bind(on_submit=lambda inst, sel, touch: self._desktop_selected(sel))
            self.popup = Popup(title="Pilih File Jadwal", content=content, size_hint=(0.9, 0.9))
            self.popup.open()

    def _desktop_selected(self, selection):
        if selection:
            self.popup.dismiss()
            self.load_file(selection[0])

    def _open_android_picker(self):
        from android import activity
        from jnius import autoclass

        Intent = autoclass("android.content.Intent")
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        if not getattr(self, "_activity_bound", False):
            activity.bind(on_activity_result=self._on_activity_result)
            self._activity_bound = True

        intent = Intent(Intent.ACTION_OPEN_DOCUMENT)
        intent.addCategory(Intent.CATEGORY_OPENABLE)
        intent.setType("*/*")
        PythonActivity.mActivity.startActivityForResult(intent, PICK_REQUEST)

    def _on_activity_result(self, request_code, result_code, intent):
        # Dipanggil dari thread Android, bukan thread Kivy.
        if request_code != PICK_REQUEST or result_code != -1 or intent is None:  # -1 = RESULT_OK
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            FileHelper = autoclass(PKG + ".FileHelper")
            path = FileHelper.copyToCache(PythonActivity.mActivity, intent.getData())
        except Exception as exc:
            msg = "Gagal membuka file: %s" % exc
            Clock.schedule_once(lambda dt: self._set_status(msg))
            return
        Clock.schedule_once(lambda dt: self.load_file(path))

    # ---------- memproses jadwal ----------
    def load_file(self, path):
        try:
            month_key, new_days = sl.load_days(path)
        except sl.ScheduleError as exc:
            self._set_status(str(exc))
            return
        except Exception as exc:
            self._set_status("Gagal membaca file: %s" % exc)
            return
        # gabungkan: bulan di file ini diganti, bulan lain (mis. bulan lalu) dipertahankan
        self.days = sl.merge_days(self.days, month_key, new_days, date.today())
        self._rebuild()
        self._save_local()
        self._push_to_widget()
        people = len({d[1] for d in new_days})
        self._set_status("%s dimuat: %d orang, bulan %s" % (os.path.basename(path), people, month_key))
        self.refresh()

    def _rebuild(self):
        self.entries = sl.build_entries(self.days)

    def refresh(self, *_):
        now = datetime.now()
        self.lbl_today.text = now.strftime("%d-%b")
        self.lbl_clock.text = now.strftime("%H:%M")
        duty, nxt = sl.compute(self.entries, now)
        self._fill(self.duty_cells, "Duty:", duty)
        self._fill(self.next_cells, "Next:", nxt)

    @staticmethod
    def _fill(row, label, items):
        # row.children terbalik urutannya (kanan -> kiri)
        cells = list(reversed(row.children))
        cells[0].text = label
        slots = items[:2]
        if len(items) > 2:  # lebih dari dua orang: "Nama +N", sama dengan widget
            slots = [items[0], (items[1][0] + " +%d" % (len(items) - 2), items[1][1])]
        for i in range(2):
            name, tm = slots[i] if i < len(slots) else (("-" if i == 0 else ""), "")
            cells[1 + 2 * i].text = name
            cells[2 + 2 * i].text = tm

    def _set_status(self, text):
        self.lbl_status.text = text

    # ---------- penyimpanan & widget ----------
    def _store_path(self):
        return os.path.join(App.get_running_app().user_data_dir, "days.txt")

    def _save_local(self):
        try:
            with open(self._store_path(), "w", encoding="utf-8") as f:
                f.write(sl.days_to_text(self.days))
        except OSError:
            pass

    def load_saved(self):
        try:
            with open(self._store_path(), "r", encoding="utf-8") as f:
                self.days = sl.text_to_days(f.read())
        except OSError:
            self.days = []
        self._rebuild()
        if self.days:
            self._set_status("Jadwal tersimpan dimuat (%d orang)" % len({d[1] for d in self.days}))
        self.refresh()

    def _push_to_widget(self):
        if platform != "android":
            return
        try:
            from jnius import autoclass
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            Provider = autoclass(PKG + ".ShiftWidgetProvider")
            ctx = PythonActivity.mActivity
            Provider.saveSchedule(ctx, sl.entries_to_text(self.entries))
            Provider.updateAll(ctx)
        except Exception as exc:
            self._set_status("Widget gagal diperbarui: %s" % exc)


class MainApp(App):
    def build(self):
        self.root_widget = ShiftApp()
        return self.root_widget

    def on_start(self):
        self.root_widget.load_saved()
        if self.root_widget.entries:
            self.root_widget._push_to_widget()
        Clock.schedule_interval(self.root_widget.refresh, 10)

    def on_pause(self):
        return True  # wajib di Android: tanpa ini aplikasi tertutup saat memilih file

    def on_resume(self):
        self.root_widget.refresh()


if __name__ == "__main__":
    MainApp().run()
