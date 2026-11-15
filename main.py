from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.popup import Popup
import pandas as pd
from datetime import datetime, timedelta

class ShiftApp(BoxLayout):
    def __init__(self, **kwargs):
        super(ShiftApp, self).__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 20
        self.spacing = 15

        # Judul Aplikasi
        self.add_widget(Label(text="[b]Aplikasi Jadwal Shift & Widget[/b]", markup=True, font_size=22, size_hint_y=None, height=40))

        # Tombol Upload File
        self.btn_upload = Button(text="Upload File Jadwal (Excel/CSV)", size_hint_y=None, height=50)
        self.btn_upload.bind(on_press=self.open_file_chooser)
        self.add_widget(self.btn_upload)

        # Label Status / Info File
        self.lbl_status = Label(text="Belum ada file yang diunggah.", size_hint_y=None, height=30)
        self.add_widget(self.lbl_status)

        # Widget Display (Sesuai Gambar Kedua)
        self.widget_box = BoxLayout(orientation='vertical', size_hint_y=None, height=180, padding=10, spacing=5)
        self.lbl_widget_title = Label(text="[b]SHIFT STATUS[/b]", markup=True, color=(1, 1, 1, 1))
        
        # Contoh Tampilan Widget Statis/Dinamis berdasarkan data
        self.lbl_duty_1 = Label(text="Duty: Dirlan | Time: 22+8")
        self.lbl_next_1 = Label(text="Next: Cum  | Time: 06:00")
        
        self.widget_box.add_widget(self.lbl_widget_title)
        self.widget_box.add_widget(self.lbl_duty_1)
        self.widget_box.add_widget(self.lbl_next_1)
        
        self.add_widget(self.widget_box)

    def open_file_chooser(self, instance):
        # Membuka file explorer sederhana untuk memilih file Excel/CSV
        content = FileChooserListView(filters=['*.xlsx', '*.xls', '*.csv'])
        content.bind(on_submit=self.load_file)
        
        self.popup = Popup(title="Pilih File Jadwal", content=content, size_hint=(0.9, 0.9))
        self.popup.open()

    def load_file(self, instance, selection, touch):
        if selection:
            file_path = selection[0]
            self.popup.dismiss()
            self.lbl_status.text = f"File dimuat: {file_path.split('/')[-1]}"
            self.process_schedule(file_path)

    def process_schedule(self, file_path):
        try:
            # Membaca file Excel atau CSV menggunakan Pandas
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Contoh logika parsing shift & kalkulasi waktu (misal: 22 + 8 jam)
            # Anda bisa menyesuaikan kolom NIK/Nama dan tanggal dari struktur tabel Anda
            sample_shift_start = 22  # Contoh jam 22:00
            added_hours = 8          # Ditambah 8 jam
            calculated_time = (sample_shift_start + added_hours) % 24
            time_result = f"{calculated_time:02d}:00" # Menjadi 06:00

            # Perbarui teks widget berdasarkan hasil pembacaan file
            self.lbl_duty_1.text = f"Duty: Dirlan (Shift {sample_shift_start}) | Time: {sample_shift_start}+{added_hours}"
            self.lbl_next_1.text = f"Next: Cum | Time: {time_result}"
            
        except Exception as e:
            self.lbl_status.text = f"Gagal membaca file: {str(e)}"

class MainApp(App):
    def build(self):
        return ShiftApp()

if __name__ == '__main__':
    MainApp().run()