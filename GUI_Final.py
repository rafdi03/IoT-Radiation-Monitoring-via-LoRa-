# pc_gui_configurable.py - GUI Konfigurasi + Logika Utama PC
import PySimpleGUI as sg # <<< TAMBAHKAN IMPORT
import serial
import time
import sys
import traceback
from time import monotonic as timer_monotonic

# ==============================================================================
# BAGIAN LOGIKA UTAMA PC (Dipindahkan ke dalam fungsi)
# ==============================================================================

# Variabel Global (tetap global agar bisa diakses fungsi)
ser_nano = None
current_data_string = None
last_read_log_line = None
last_send_time_mono = None
data_waiting_to_be_sent = False # Flag ini sebenarnya kurang relevan di versi terakhir

# Gunakan variabel dari config alih-alih global hardcoded untuk parameter ini
# SERIAL_PORT_NANO = "COM14"
# BAUD_RATE = 9600
# LOG_FILE_PATH = r"C:\Users\aryag\Documents\SKRIPSI\datarpm.log.txt"
# NUM_CHUNKS = 1
# EXPECTED_LOG_FIELDS = 11
# NANO_RESPONSE_TIMEOUT = 10.0

def print_debug(message):
    timestamp = time.strftime("%H:%M:%S")
    print(f"[{timestamp} PC DEBUG] {message}", flush=True); sys.stdout.flush()

def read_last_line_csv(file_path):
    """Membaca baris terakhir yang tidak kosong dari file CSV."""
    if not file_path or not os.path.exists(file_path): # <<< Tambah cek path
        print_debug(f"Error: File log path tidak valid atau tidak ditemukan: {file_path}")
        return None
    try:
        with open(file_path, 'rb') as f:
            f.seek(0, 2); file_size = f.tell()
            if file_size == 0: print_debug("Log file kosong."); return None
            search_offset = min(file_size, 2048); f.seek(-search_offset, 2)
            buffer = f.read(search_offset).splitlines()
            for i in range(len(buffer) - 1, -1, -1):
                try:
                    line_str = buffer[i].decode('utf-8', errors='ignore').strip()
                    if line_str and ',' in line_str: return line_str
                except: continue
            if file_size <= search_offset:
                f.seek(0); first_line_bytes = f.readline()
                try: line_str = first_line_bytes.decode('utf-8', errors='ignore').strip(); return line_str if line_str and ',' in line_str else None
                except: pass
            print_debug("Tidak ada baris CSV valid ditemukan."); return None
    # FileNotFoundError sudah ditangani di cek awal
    except Exception as e: print_debug(f"Error baca baris terakhir: {e}"); return None

def extract_data_from_csv_log(line, expected_fields): # <<< Tambah argumen expected_fields
    """Ekstrak data relevan dari baris log CSV."""
    if not line: return None
    try:
        fields = line.split(',')
        # Gunakan expected_fields dari argumen
        if len(fields) < expected_fields:
            print_debug(f"WARN: Field ({len(fields)}) < diharapkan ({expected_fields}). Skip: {line[:50]}..."); return None
        # Asumsi format: Timestamp,Pilar1,B1p1,B2p1,L1p1,L2p1,Pilar2,B1p2,B2p2,L1p2,L2p2 (11 fields)
        # Jika expected_fields berbeda, logika ekstraksi ini perlu PENYESUAIAN!
        if expected_fields == 11: # Contoh penyesuaian jika field berbeda
            timestamp=fields[0]; b1_p1=fields[2]; b2_p1=fields[3]; l1_p1=fields[4]; l2_p1=fields[5]; b1_p2=fields[7]; b2_p2=fields[8]; l1_p2=fields[9]; l2_p2=fields[10]
            # Format data untuk dikirim (sesuaikan urutan/field yang diambil)
            data_to_send = [ timestamp, b1_p1, b2_p1, l1_p1, l2_p1, b1_p2, b2_p2, l1_p2, l2_p2 ] # Kirim 9 field
        else:
            # Logika default jika field bukan 11 (misal, ambil semua)
            print_debug(f"WARN: Menggunakan logika ekstraksi default karena expected_fields={expected_fields}")
            data_to_send = [f.strip() for f in fields] # Ambil semua field
            # Anda mungkin perlu logika berbeda di sini tergantung format lain

        print_debug(f"Data diekstrak ({len(data_to_send)} fields dikirim): {','.join(data_to_send)[:80]}...")
        return ",".join(map(str, data_to_send))
    except IndexError as ie: print_debug(f"Error Indeks ekstrak CSV: {ie} (Expected: {expected_fields}, Got: {len(fields)})"); return None
    except Exception as e: print_debug(f"Error ekstrak CSV: {e}"); return None

def send_data_to_nano(data_str, nano_timeout): # <<< Tambah argumen nano_timeout
    """Mengirim string data tunggal sebagai CHUNK:1 dan update timer."""
    global last_send_time_mono, ser_nano # Akses serial global
    if not ser_nano or not ser_nano.is_open: print_debug("Error: Serial port tidak terbuka."); return False
    if not data_str: print_debug("Error: Tidak ada data untuk dikirim."); return False
    message = f"CHUNK:1:{data_str}\n"
    try:
        preview = data_str[:80] + ('...' if len(data_str) > 80 else '')
        print_debug(f"Mengirim ke Nano: CHUNK:1:<{preview}>")
        ser_nano.write(message.encode('utf-8')); ser_nano.flush()
        last_send_time_mono = timer_monotonic()
        # Gunakan nano_timeout dari argumen
        print_debug(f"Data terkirim. Menunggu {nano_timeout:.1f} detik untuk respon/request Nano berikutnya...")
        return True
    except Exception as e:
        print_debug(f"Error kirim data: {e}")
        last_send_time_mono = None
        return False

def process_get_data_command(log_file_path, expected_log_fields): # <<< Tambah argumen
    """Proses 'get_data': baca log, ekstrak, siapkan data."""
    global current_data_string, last_read_log_line, data_waiting_to_be_sent
    print_debug("Memproses 'get_data': Baca file log CSV...")
    # Gunakan argumen path
    new_log_line = read_last_line_csv(log_file_path)
    if not new_log_line: print_debug("Gagal baca log."); current_data_string = None; last_read_log_line = None; data_waiting_to_be_sent = False; return False

    data_changed = (new_log_line != last_read_log_line)
    should_extract = data_changed or not current_data_string

    if should_extract:
        if data_changed: print_debug("Log baru. Ekstrak data...")
        else: print_debug("Data kosong. Ekstrak ulang...")
        # Gunakan argumen expected fields
        extracted_data = extract_data_from_csv_log(new_log_line, expected_log_fields)
        if extracted_data:
            current_data_string = extracted_data; last_read_log_line = new_log_line
            # data_waiting_to_be_sent = True # Tidak perlu lagi karena langsung kirim
            print_debug("Ekstraksi data berhasil. Siap dikirim.")
            return True
        else: print_debug("Gagal ekstrak data."); current_data_string = None; data_waiting_to_be_sent = False; return False
    else:
        print_debug("Log sama. Gunakan data sebelumnya.")
        if not current_data_string: print_debug("ERROR: Log sama tapi data kosong!"); data_waiting_to_be_sent = False; return False
        # data_waiting_to_be_sent = True # Tidak perlu lagi
        print_debug("Data sebelumnya siap dikirim ulang.")
        return True

def reset_pc_state(reason=""):
    """Fungsi untuk mereset state PC."""
    global current_data_string, last_read_log_line, last_send_time_mono, data_waiting_to_be_sent
    print_debug(f"RESETTING PC STATE. Reason: {reason}")
    current_data_string = None
    last_send_time_mono = None
    data_waiting_to_be_sent = False
    print_debug("State PC direset. Menunggu 'get_data' baru...")

# --- Fungsi Logika Utama (Menerima Konfigurasi) ---
def run_main_logic(config):
    """Menjalankan logika utama komunikasi serial dengan konfigurasi yang diberikan."""
    global ser_nano, current_data_string, last_read_log_line, last_send_time_mono, data_waiting_to_be_sent

    # Ambil nilai konfigurasi dari dictionary
    serial_port = config['SERIAL_PORT_NANO']
    baud_rate = config['BAUD_RATE']
    log_file_path = config['LOG_FILE_PATH']
    expected_log_fields = config['EXPECTED_LOG_FIELDS']
    nano_timeout = config['NANO_RESPONSE_TIMEOUT']
    # num_chunks tidak digunakan lagi di versi ini

    print_debug("Memulai logika utama dengan konfigurasi:")
    print_debug(f"  Port: {serial_port}, Baud: {baud_rate}")
    print_debug(f"  Log: {log_file_path} (Harap {expected_log_fields} fields)")
    print_debug(f"  Timeout Nano: {nano_timeout}s")

    # --- Inisialisasi Serial ---
    while ser_nano is None:
        try:
            # Gunakan variabel dari config
            ser = serial.Serial(serial_port, baud_rate, timeout=1, write_timeout=2)
            ser_nano = ser; time.sleep(2); ser_nano.reset_input_buffer()
            print_debug(f"Membuka {serial_port}...")
        except serial.SerialException as e: # Lebih spesifik
             print_debug(f"Error buka serial {serial_port}: {e}. Coba lagi 5d...")
             time.sleep(5)
        except Exception as e: # Error lain saat init
             print_debug(f"Error fatal saat inisialisasi serial: {e}")
             sg.popup_error(f"Gagal membuka port serial {serial_port}:\n{e}\n\nPastikan port benar dan tidak digunakan program lain.")
             return # Keluar dari fungsi jika serial gagal dibuka

    # Reset state awal
    reset_pc_state("Startup")

    # --- Loop Utama ---
    try:
        while True:
            current_time_mono = timer_monotonic()

            try:
                # --- Cek & Handle Koneksi ---
                if not ser_nano or not ser_nano.is_open:
                     print_debug("Serial terputus. Mencoba konek ulang..."); ser_nano = None; reset_pc_state("Serial Disconnect")
                     while ser_nano is None:
                        try:
                            # Gunakan variabel dari config lagi saat reconnect
                            ser = serial.Serial(serial_port, baud_rate, timeout=1, write_timeout=2)
                            ser_nano = ser; time.sleep(2); ser_nano.reset_input_buffer(); print_debug(f"Konek ulang ke {serial_port}.")
                        except serial.SerialException: time.sleep(5)
                        except Exception as recon_e: print_debug(f"Error konek ulang: {recon_e}"); time.sleep(5)
                     print_debug("Menunggu komunikasi Nano..."); continue

                # --- Baca dari Nano ---
                if ser_nano.in_waiting > 0:
                    data_raw = b''; data = ''
                    try:
                        data_raw = ser_nano.readline()
                        if not data_raw: continue
                        data = data_raw.decode('utf-8', errors='ignore').strip()
                        if not data: continue
                        if data.startswith(("[NANO", "---")): continue

                        print_debug(f"RX Nano: '{data}'")

                        # --- Proses Perintah ---
                        if data == "get_data":
                            last_send_time_mono = None # Reset timer timeout
                            print_debug("--> 'get_data' diterima. Proses log...")
                            # Pass config values ke fungsi proses
                            if process_get_data_command(log_file_path, expected_log_fields):
                                # Pass config timeout ke fungsi kirim
                                if not send_data_to_nano(current_data_string, nano_timeout):
                                    print_debug("ERROR: Gagal kirim data post 'get_data'.")
                                    reset_pc_state("Send fail after get_data")
                                # else: Pengiriman berhasil, timer sudah diset
                            else: print_debug("ERROR: Gagal siapkan data.")
                        elif data == "next":
                            print_debug("--> 'next' diterima. Abaikan (single chunk).")
                            last_send_time_mono = None # Reset timer timeout
                        else: print_debug(f"Perintah tidak dikenal: '{data}'")

                    except UnicodeDecodeError as decode_err: print_debug(f"Serial decode error: {decode_err}. Raw: {data_raw}")
                    except Exception as proc_e: print_debug(f"Error proses pesan Nano: {proc_e}"); traceback.print_exc()

                # --- Cek Timeout Nano Response ---
                if last_send_time_mono is not None:
                    time_since_last_send = current_time_mono - last_send_time_mono
                    # Gunakan config timeout
                    if time_since_last_send > nano_timeout:
                        print_debug(f"TIMEOUT! > {nano_timeout:.1f} detik sejak kirim, tidak ada respon/request Nano.")
                        reset_pc_state("Nano Timeout")
                        try: # Flush buffer
                            if ser_nano and ser_nano.is_open: ser_nano.reset_input_buffer(); print_debug("Input buffer serial di-flush.")
                        except Exception as flush_e: print_debug(f"Error flush input buffer: {flush_e}")

                time.sleep(0.05) # Delay

            except serial.SerialException as se:
                print_debug(f"Serial error di loop: {se}. Menangani...")
                if ser_nano and ser_nano.is_open:
                    try: ser_nano.close()
                    except: pass
                ser_nano = None; reset_pc_state("SerialException in loop")
                print_debug("Tunggu 2d sebelum reconnect..."); time.sleep(2); continue
            except Exception as loop_e:
                print_debug(f"Error tak terduga di loop: {loop_e}"); traceback.print_exc()
                reset_pc_state(f"Unexpected Loop Error: {loop_e}")
                print_debug("Tunggu 5d..."); time.sleep(5)

    except KeyboardInterrupt: print_debug("\nKeluar.")
    except Exception as fatal_e: print_debug(f"FATAL ERROR: {fatal_e}"); traceback.print_exc()
    finally:
         # Akses ser_nano global untuk cleanup
         if ser_nano and ser_nano.is_open:
             try: ser_nano.close(); print_debug("Serial ditutup.")
             except Exception as close_e: print_debug(f"Error tutup serial: {close_e}")
         print_debug("Skrip PC selesai.")


# ==============================================================================
# BAGIAN GUI PYSimpleGUI
# ==============================================================================
import PySimpleGUI as sg
import os # Import os untuk cek path

# Set tema (opsional)
sg.theme('SystemDefaultForReal') # Coba tema default sistem

# Nilai default untuk form (ambil dari konstanta awal jika ada, atau set manual)
default_com = "COM14"
default_baud = "9600"
default_log_path = r"C:\Users\aryag\Documents\SKRIPSI\datarpm.log.txt"
default_chunks = "1"
default_fields = "11"
default_timeout = "10.0"

# Layout form GUI
layout = [
    [sg.Text('Konfigurasi Komunikasi PC', font='_ 14')],
    [sg.HorizontalSeparator()],
    [sg.Text('Port Serial Nano', size=(25,1)), sg.InputText(default_com, key='-COM-', size=(20,1))],
    [sg.Text('Baud Rate', size=(25,1)), sg.InputText(default_baud, key='-BAUD-', size=(20,1))],
    [sg.Text('Path File Log (.csv/.txt)', size=(25,1)), sg.InputText(default_log_path, key='-LOGPATH-', size=(40,1)), sg.FileBrowse(target='-LOGPATH-')], # Tombol browse
    [sg.Text('Jumlah Chunk (Harus 1)', size=(25,1)), sg.InputText(default_chunks, key='-CHUNKS-', size=(5,1), readonly=True, disabled_readonly_background_color='lightgrey')], # Baca saja
    [sg.Text('Jumlah Field Log Diharapkan', size=(25,1)), sg.InputText(default_fields, key='-FIELDS-', size=(5,1))],
    [sg.Text('Timeout Respons Nano (detik)', size=(25,1)), sg.InputText(default_timeout, key='-TIMEOUT-', size=(10,1))],
    [sg.HorizontalSeparator()],
    [sg.Submit('Jalankan Proses', key='-SUBMIT-'), sg.Cancel('Batal', key='-CANCEL-')]
]

# Buat window
window = sg.Window('Konfigurasi PC Logger', layout, finalize=True) # finalize=True agar bisa disable

# Loop event GUI
config_data = None # Untuk menyimpan konfigurasi jika valid

while True:
    event, values = window.read()

    if event == sg.WIN_CLOSED or event == '-CANCEL-':
        print("Aksi dibatalkan oleh pengguna.")
        break # Keluar dari loop GUI

    if event == '-SUBMIT-':
        # Validasi Input
        try:
            com_port = values['-COM-']
            if not com_port: raise ValueError("COM Port tidak boleh kosong.")

            baud_rate = int(values['-BAUD-'])
            if baud_rate <= 0: raise ValueError("Baud Rate harus positif.")

            log_path = values['-LOGPATH-']
            if not log_path: raise ValueError("Path File Log tidak boleh kosong.")
            # Cek sederhana apakah file (mungkin) ada, tapi read_last_line akan cek lagi
            # if not os.path.exists(log_path): print(f"Warning: File log di '{log_path}' tidak ditemukan saat ini.") # Warning saja

            num_chunks = int(values['-CHUNKS-']) # Ambil dari field (meski readonly)
            if num_chunks != 1: raise ValueError("Jumlah Chunk harus 1 untuk skrip ini.")

            expected_fields = int(values['-FIELDS-'])
            if expected_fields <= 0: raise ValueError("Jumlah Field harus positif.")

            nano_timeout = float(values['-TIMEOUT-'])
            if nano_timeout <= 0: raise ValueError("Timeout harus positif.")

            # Jika semua valid, simpan konfigurasi
            config_data = {
                'SERIAL_PORT_NANO': com_port,
                'BAUD_RATE': baud_rate,
                'LOG_FILE_PATH': log_path,
                'NUM_CHUNKS': num_chunks, # Tetap simpan meski hanya 1
                'EXPECTED_LOG_FIELDS': expected_fields,
                'NANO_RESPONSE_TIMEOUT': nano_timeout
            }
            sg.popup_quick_message('Konfigurasi diterima, menjalankan proses...', background_color='green', text_color='white', auto_close_duration=2)
            break # Keluar dari loop GUI untuk jalankan proses

        except ValueError as ve: # Error konversi tipe data atau validasi
            sg.popup_error(f"Input tidak valid: {ve}\nMohon periksa kembali nilai yang dimasukkan.", title="Error Input")
        except Exception as e: # Error tak terduga lain
            sg.popup_error(f"Terjadi kesalahan saat validasi input:\n{e}", title="Error")

# Tutup window GUI setelah loop selesai
window.close()

# Jalankan logika utama HANYA jika konfigurasi berhasil didapat
if config_data:
    print("-" * 50)
    print("Memulai Proses Utama dengan Konfigurasi dari GUI...")
    print("-" * 50)
    run_main_logic(config_data) # Panggil fungsi utama dengan konfigurasi
else:
    print("Tidak ada konfigurasi valid yang didapat dari GUI. Skrip berhenti.")

print("\nProgram Selesai.")