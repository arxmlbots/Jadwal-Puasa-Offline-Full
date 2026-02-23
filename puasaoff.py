import time
import datetime
import requests
import json
import os
from colorama import Fore, Style, init

# Optional: fallback offline Hijri
try:
    from hijri_converter import Gregorian
    hijri_converter_available = True
except:
    hijri_converter_available = False

init(autoreset=True)
os.system('clear' if os.name == 'posix' else 'cls')

# ================= KONFIGURASI =================
city = "" # ISI DENGAN NAMA KOTA KAMU MASING - MASING!
country = "ID"
DATA_FILE_TEMPLATE = "jadwal_tahunan_{}.json"  # akan diisi tahun

# ================= FUNGSI AMBIL DATA TAHUNAN DARI API =================
def fetch_yearly_prayer_times(city, country, year):
    """
    Mengambil jadwal sholat untuk seluruh bulan dalam tahun tertentu.
    Mengembalikan dictionary dengan format:
    {
        "YYYY-MM-DD": {
            "Sahur": "HH:MM",
            "Imsak": "HH:MM",
            "Subuh": "HH:MM",
            "Sunrise": "HH:MM",
            "Dzuhur": "HH:MM",
            "Ashar": "HH:MM",
            "Sunset": "HH:MM",
            "Maghrib": "HH:MM",
            "Isya": "HH:MM",
            "Tarawih": "HH:MM",
            "Midnight": "HH:MM"
        },
        ...
    }
    """
    print(f"Mengambil data jadwal tahun {year} dari API...")
    jadwal_tahunan = {}
    
    for month in range(1, 13):
        url = f"http://api.aladhan.com/v1/calendarByCity"
        params = {
            "city": city,
            "country": country,
            "method": 2,
            "month": month,
            "year": year
        }
        try:
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            if data["code"] == 200:
                for day_data in data["data"]:
                    gregorian_date = day_data["date"]["gregorian"]["date"]  # format: DD-MM-YYYY
                    # Ubah ke YYYY-MM-DD agar mudah diurutkan
                    d, m, y = gregorian_date.split("-")
                    date_key = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                    
                    timings = day_data["timings"]
                    jadwal_harian = {
                        "Sahur": timings["Lastthird"][:5],	 # Sahur dulu bang :v
                        "Imsak": timings["Imsak"][:5],  	 # Imsak bang
                        "Subuh": timings["Fajr"][:5],		 # Adzan subuh cuy
                        "Sunrise": timings["Sunrise"][:5],	 # Matahari Terbit cuy segerakan untuk berjemur badan 😉
                        "Dzuhur": timings["Dhuhr"][:5],		 # Adzan Dzuhur cuy
                        "Ashar": timings["Asr"][:5],		 # Adzan Ashar ini mah 
                        "Sunset": timings["Sunset"][:5],	 # Matahari Terbanam cuy lumayan takjil gratisss
                        "Maghrib": timings["Maghrib"][:5],	 # Adzan magrib jangan KELUYURAN!
                        "Isya": timings["Isha"][:5],		 # Adzan Isya shalat
                        "Tarawih": timings["Isha"][:5],  	 # Tarawih sama dengan Isya yaa
                        "Midnight": timings["Midnight"][:5]	 # Tengah malam harus bobok kamu 😘
                    }
                    jadwal_tahunan[date_key] = jadwal_harian
                print(f"  Bulan {month:02d} selesai.")
            else:
                print(f"  Gagal mengambil bulan {month}: {data['code']}")
        except Exception as e:
            print(f"  Error bulan {month}: {e}")
        
        time.sleep(1)  # jeda agar tidak kena rate limit
    
    print(f"Total {len(jadwal_tahunan)} hari berhasil diambil.")
    return jadwal_tahunan

def load_or_fetch_data():
    """
    Memuat data dari file jika ada dan tahunnya sesuai.
    Jika tidak, ambil dari API dan simpan ke file.
    Mengembalikan tuple (data_tahunan, tahun_data)
    """
    now = datetime.datetime.now()
    tahun_sekarang = now.year
    filename = DATA_FILE_TEMPLATE.format(tahun_sekarang)
    
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
            print(f"Memuat data dari file {filename}")
            # Cek apakah data cukup (misal setidaknya 300 hari)
            if len(data) > 300:
                return data, tahun_sekarang
            else:
                print("Data di file tidak lengkap, akan ambil ulang.")
        except:
            print("Gagal membaca file, akan ambil ulang.")
    
    # Ambil dari API
    data = fetch_yearly_prayer_times(city, country, tahun_sekarang)
    if data:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        print(f"Data disimpan ke {filename}")
        return data, tahun_sekarang
    else:
        print("Gagal mengambil data dari API.")
        return None, None

# ================= FUNGSI TANGGAL HIJRIAH (tetap pakai API atau fallback) =================
def get_hijri_date():
    try:
        url = "http://api.aladhan.com/v1/gToH"
        today = datetime.datetime.now().strftime("%d-%m-%Y")
        response = requests.get(f"{url}?date={today}", timeout=5)
        data = response.json()
        hijri = data.get("data", {}).get("hijri", None)
        if hijri:
            day = hijri.get("day", "?")
            month = hijri.get("month", {}).get("en", "?")
            year = hijri.get("year", "?")
            return f"{day} {month} {year} H"
        else:
            raise Exception("API gagal")
    except:
        if hijri_converter_available:
            h = Gregorian.today().to_hijri()
            return f"{h.day} {h.month_name()} {h.year} H"
        else:
            return "N/A"

# ================= FUNGSI MENAMPILKAN TABEL =================
def print_table(jadwal_harian, next_sholat):
    """
    Mencetak tabel sholat berdasarkan jadwal hari ini.
    jadwal_harian: dictionary dengan key nama sholat dan value waktu (HH:MM)
    next_sholat: nama sholat berikutnya (string) untuk highlight
    """
    # Urutan tampilan
    urutan = ["Sahur", "Imsak", "Subuh", "Sunrise", "Dzuhur", "Ashar", "Sunset", "Maghrib", "Buka Puasa", "Isya", "Tarawih", "Midnight"]
    
    print(f"{Fore.WHITE}+----------------+--------+")
    print(f"{Fore.WHITE}| {Fore.BLUE}Sholat/Tanggal {Fore.WHITE}| {Fore.BLUE}Waktu  {Fore.WHITE}|")
    print(f"{Fore.WHITE}+----------------+--------+")
    
    for nama in urutan:
        if nama == "Buka Puasa":
            waktu = jadwal_harian.get("Maghrib", "??:??")
            # Highlight jika next_sholat adalah Maghrib (karena buka puasa sama)
            highlight = (next_sholat == "Maghrib")
        else:
            waktu = jadwal_harian.get(nama, "??:??")
            highlight = (nama == next_sholat)
        
        if highlight:
            line = f"{Fore.RED}| {nama:<14} | {waktu:<6} |"
        else:
            line = f"{Fore.WHITE}| {nama:<14} | {waktu:<6} |"
        print(line)
    
    print(f"{Fore.WHITE}+----------------+--------+")

# ================= FUNGSI MENENTUKAN SHOLAT BERIKUTNYA =================
def get_next_sholat(jadwal_harian, sekarang, data_tahunan, tanggal_sekarang):
    """
    Menentukan nama sholat berikutnya dan waktu objek datetime-nya.
    Mempertimbangkan jika semua sholat hari ini sudah lewat, ambil sholat pertama besok.
    """
    # Daftar sholat dalam urutan kronologis (tanpa duplikat Buka Puasa)
    urutan_sholat = ["Sahur", "Imsak", "Subuh", "Sunrise", "Dzuhur", "Ashar", "Sunset", "Maghrib", "Buka Puasa", "Isya", "Tarawih", "Midnight"]
    
    # Buat list (waktu, nama) untuk hari ini
    daftar = []
    for nama in urutan_sholat:
        waktu_str = jadwal_harian.get(nama)
        if waktu_str:
            waktu_obj = datetime.datetime.strptime(waktu_str, "%H:%M").replace(
                year=sekarang.year, month=sekarang.month, day=sekarang.day
            )
            daftar.append((waktu_obj, nama))
    
    # Urutkan berdasarkan waktu (seharusnya sudah urut, tapi amankan)
    daftar.sort()
    
    # Cari yang pertama kali setelah sekarang
    for waktu_obj, nama in daftar:
        if sekarang < waktu_obj:
            return nama, waktu_obj
    
    # Jika semua sudah lewat, cari sholat pertama besok (imsak)
    besok = sekarang + datetime.timedelta(days=1)
    tgl_besok = besok.strftime("%Y-%m-%d")
    jadwal_besok = data_tahunan.get(tgl_besok)
    if jadwal_besok:
        # Ambil Sahur besok
        waktu_imsak_str = jadwal_besok.get("Sahur")
        if waktu_imsak_str:
            waktu_imsak = datetime.datetime.strptime(waktu_imsak_str, "%H:%M").replace(
                year=besok.year, month=besok.month, day=besok.day
            )
            return "Sahur", waktu_sahur
    
    # Tidak ada data untuk besok
    return None, None

# ================= ANIMASI LAMPU =================
def running_lamp():
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.MAGENTA]
    for i in range(5):
        color = colors[i % len(colors)]
        print(color + "▓" * 50, end="\r")
        time.sleep(0.1)

# ================= PROGRAM UTAMA =================
def main():
    # Load atau fetch data tahunan
    data_tahunan, tahun_data = load_or_fetch_data()
    if not data_tahunan:
        print("Tidak dapat memperoleh data jadwal. Pastikan koneksi internet untuk pengambilan pertama.")
        return
    
    # Judul
    print(judul)
    
    # Variabel untuk menyimpan tanggal terakhir yang ditampilkan
    last_date_str = ""
    last_next_sholat = None
    last_next_time = None
    
    # Loop utama
    try:
        while True:
            now = datetime.datetime.now()
            tanggal_str = now.strftime("%Y-%m-%d")
            
            # Cek apakah tahun berganti
            if now.year != tahun_data:
                print("\nTahun berganti, memperbarui data...")
                data_tahunan, tahun_data = load_or_fetch_data()
                if not data_tahunan:
                    print("Gagal memperbarui data. Melanjutkan dengan data lama.")
                last_date_str = ""  # paksa refresh tampilan
            
            # Ambil jadwal hari ini
            jadwal_hari_ini = data_tahunan.get(tanggal_str)
            if not jadwal_hari_ini:
                # Jika tanggal tidak ada (misal 31 Februari), fallback ke data terdekat?
                print(f"Peringatan: Jadwal untuk {tanggal_str} tidak ditemukan.")
                # Bisa gunakan data kemarin atau kosong
                jadwal_hari_ini = {
                    "Imsak": "--:--",
                    "Subuh": "--:--",
                    "Dzuhur": "--:--",
                    "Ashar": "--:--",
                    "Maghrib": "--:--",
                    "Isya": "--:--",
                    "Tarawih": "--:--"
                }
            
            # Tentukan sholat berikutnya
            next_sholat, next_time = get_next_sholat(jadwal_hari_ini, now, data_tahunan, tanggal_str)
            
            # Jika tanggal berubah atau next_sholat berubah, cetak ulang tabel
            if tanggal_str != last_date_str or next_sholat != last_next_sholat:
                os.system('clear' if os.name == 'posix' else 'cls')
                print(judul)
                hari = now.strftime("%A")
                tanggal = now.strftime("%d-%m-%Y")
                hijri = get_hijri_date()
                print(f"{Fore.WHITE}Hari/Tanggal : {hari}, {tanggal}")
                print(f"Tanggal Hijriah : {hijri}\n")
                print_table(jadwal_hari_ini, next_sholat)
                print("\n")  # dua baris kosong
                last_date_str = tanggal_str
                last_next_sholat = next_sholat
                last_next_time = next_time
                
                # Simpan posisi cursor (setelah tabel dan 2 baris kosong)
                print("\033[s", end="")
            
            # Update jam dan countdown (2 baris di atas posisi cursor)
            jam = now.strftime("%H:%M:%S")
            if next_time:
                diff = next_time - now
                if diff.total_seconds() > 0:
                    total_seconds = int(diff.total_seconds())
                    jam_countdown = total_seconds // 3600
                    sisa = total_seconds % 3600
                    menit = sisa // 60
                    detik = sisa % 60
                    countdown = f"Waktu menuju {next_sholat}: {jam_countdown} jam {menit} menit {detik} detik"
                else:
                    countdown = f"{next_sholat} sudah lewat"
            else:
                countdown = "Tidak ada jadwal sholat berikutnya"
            
            # Update dua baris di atas posisi cursor (yang disimpan)
            print("\033[2A", end="")          # naik 2 baris dari posisi simpan
            print(f"\rWaktu sekarang : {jam}{' ' * 40}")
            print(f"\r{countdown}{' ' * 40}")
            print("\033[u", end="")            # kembali ke posisi simpan
            
            # Animasi lampu
            running_lamp()
            
            time.sleep(0.1)  # sedikit tidur agar tidak terlalu berat
    
    except KeyboardInterrupt:
        print("\n\nProgram berhenti. Ramadan Mubarak! 🌙")

# ================= JUDUL =================
judul = f"""
{Fore.WHITE}{'*'*50}
{Fore.BLUE}           RAMADAN DASHBOARD  (OFFLINE)
{Fore.WHITE}{'*'*50}
"""

if __name__ == "__main__":
    main()
    