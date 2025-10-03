 
import serial 
import time 
import sys 
import os 
from time import monotonic as timer_monotonic 
 
# --- Konfigurasi --- 
# PENTING: Ganti nilai ini dengan COM Port Arduino Nano Anda di Windows 
SERIAL_PORT_NANO = "COM3" 
BAUD_RATE = 9600 
 
# PENTING: Ganti nilai ini dengan path absolut ke file log CSV Anda 
LOG_FILE_PATH = r"C:\Users\YourUser\Documents\data_log.csv" 
EXPECTED_LOG_FIELDS = 11 # Jumlah kolom yang diharapkan di file CSV 
NANO_RESPONSE_TIMEOUT = 7.0 # Timeout menunggu permintaan dari Nano 
 
# --- Variabel Global --- 
ser_nano = None 
current_data_string = None 
last_read_log_line = None 
last_send_time_mono = None 
 
 
 
 
 
 
# --- Fungsi Cetak Debug --- 
def print_debug(message): 
    """Mencetak pesan debug dengan timestamp.""" 
    timestamp = time.strftime("%H:%M:%S") 
    print(f"[{timestamp} PC DEBUG] {message}", flush=True) 
 
# --- Fungsi Baca Baris Terakhir CSV --- 
def read_last_line_csv(file_path): 
    """Membaca baris terakhir yang tidak kosong dari file CSV.""" 
    if not file_path or not os.path.exists(file_path): 
        print_debug(f"Error: Path file log tidak valid atau tidak ditemukan: 
{file_path}") 
        return None 
    try: 
        with open(file_path, 'rb') as f: 
            f.seek(0, 2) 
            if f.tell() == 0: return None # File kosong 
            f.seek(-min(f.tell(), 2048), 2) 
            lines = f.read().splitlines() 
            for line in reversed(lines): 
                line_str = line.decode('utf-8', errors='ignore').strip() 
                if line_str and ',' in line_str: 
                    return line_str 
        return None 
    except Exception as e: 
        print_debug(f"Error saat membaca baris terakhir: {e}") 
        return None 
 
# --- Fungsi Ekstraksi Data dari CSV --- 
def extract_data_from_csv_log(line, expected_fields): 
    """Mengekstrak field data yang relevan dari satu baris log CSV.""" 
    if not line: return None 
    try: 
        fields = line.split(',') 
        if len(fields) < expected_fields: 
            print_debug(f"PERINGATAN: Jumlah field ({len(fields)}) < diharapkan 
({expected_fields}).") 
            return None 
         
        # Asumsi format CSV: 
Timestamp,Pilar1,B1p1,B2p1,L1p1,L2p1,Pilar2,B1p2,B2p2,L1p2,L2p2 
        # Ekstrak data yang dibutuhkan untuk dikirim ke Pi 
        timestamp = fields[0].strip() 
        b1_p1, b2_p1, l1_p1, l2_p1 = fields[2].strip(), fields[3].strip(), 
fields[4].strip(), fields[5].strip() 
        b1_p2, b2_p2, l1_p2, l2_p2 = fields[7].strip(), fields[8].strip(), 
fields[9].strip(), fields[10].strip() 
 
        # Gabungkan data ke dalam satu string, siap kirim 
        data_to_send = [timestamp, b1_p1, b2_p1, l1_p1, l2_p1, b1_p2, b2_p2, 
l1_p2, l2_p2] 
        return ",".join(map(str, data_to_send)) 
    except (IndexError, ValueError) as e: 
        print_debug(f"Error saat mengekstrak data dari log CSV: {e}") 
        return None 
 
# --- Fungsi Kirim Data ke Nano --- 
def send_data_to_nano(data_str): 
    """Mengirim data dengan format 'CHUNK:1:<data>' ke Arduino Nano.""" 
    global last_send_time_mono 
    if not ser_nano or not ser_nano.is_open: 
        print_debug("Error: Port serial tidak terbuka."); return False 
     
    message = f"CHUNK:1:{data_str}\n" 
    try: 
        message_bytes = message.encode('utf-8') 
        bytes_written = ser_nano.write(message_bytes) 
        ser_nano.flush() 
        print_debug(f"Mengirim ke Nano: CHUNK:1:<{data_str[:60]}...>") 
        print_debug(f"  -> Berhasil mengirim {bytes_written} bytes.") 
        last_send_time_mono = timer_monotonic() 
        return True 
    except Exception as e: 
 
 
 
 
 
        print_debug(f"Error mengirim data: {e}") 
        return False 
 
# --- Fungsi Proses Perintah 'get_data' --- 
def process_get_data_command(): 
    """Memproses perintah 'get_data' dengan membaca log dan menyiapkan data.""" 
    global current_data_string, last_read_log_line 
    print_debug("Memproses 'get_data': Membaca file log CSV...") 
    new_log_line = read_last_line_csv(LOG_FILE_PATH) 
    if not new_log_line: 
        print_debug("Gagal membaca log atau file kosong."); return False 
 
    # Hanya ekstrak ulang jika data di log berubah 
    if new_log_line != last_read_log_line: 
        print_debug("Log baru terdeteksi. Mengekstrak data...") 
        extracted_data = extract_data_from_csv_log(new_log_line, 
EXPECTED_LOG_FIELDS) 
        if extracted_data: 
            current_data_string = extracted_data 
            last_read_log_line = new_log_line 
            print_debug("Ekstraksi data berhasil. Siap dikirim.") 
            return True 
        else: 
            print_debug("Gagal mengekstrak data."); return False 
    else: 
        print_debug("Log tidak berubah. Menggunakan data sebelumnya.") 
        return True if current_data_string else False 
 
# --- Fungsi Reset State PC --- 
def reset_pc_state(reason=""): 
    """Mereset state operasional PC.""" 
    global current_data_string, last_send_time_mono 
    print_debug(f"MERESET STATE PC. Alasan: {reason}") 
    current_data_string = None 
    last_send_time_mono = None 
 
# --- Loop Program Utama --- 
def main(): 
    global ser_nano 
    while ser_nano is None: 
        try: 
            ser_nano = serial.Serial(SERIAL_PORT_NANO, BAUD_RATE, Timeout=1, 
write_Timeout=2) 
            time.sleep(2) 
            ser_nano.reset_input_buffer() 
            print_debug(f"Berhasil membuka port {SERIAL_PORT_NANO}...") 
        except serial.SerialException as e: 
            print_debug(f"Error membuka port {SERIAL_PORT_NANO}: {e}. Mencoba 
lagi dalam 5 detik...") 
            time.sleep(5) 
 
    reset_pc_state("Startup") 
 
    while True: 
        try: 
            if ser_nano.in_waiting > 0: 
                data_raw = ser_nano.readline() 
                if data_raw: 
                    data = data_raw.decode('utf-8', errors='ignore').strip() 
                    if data == "get_data": 
                        last_send_time_mono = None 
                        if process_get_data_command(): 
                            if not send_data_to_nano(current_data_string): 
                                reset_pc_state("Gagal kirim setelah get_data") 
                        else: 
                            print_debug("ERROR: Gagal menyiapkan data.") 
             
            # Cek Timeout dari Nano 
            if last_send_time_mono and (timer_monotonic() - last_send_time_mono 
> NANO_RESPONSE_TIMEOUT): 
                print_debug(f"TIMEOUT! > {NANO_RESPONSE_TIMEOUT:.1f} detik, 
tidak ada permintaan baru dari Nano.") 
                reset_pc_state("Timeout Nano") 
 
 
 
 
 
 
            time.sleep(0.05) 
        except serial.SerialException as se: 
            print_debug(f"Serial error: {se}. Mencoba menyambung ulang...") 
            if ser_nano and ser_nano.is_open: ser_nano.close() 
            ser_nano = None; reset_pc_state("Serial Error"); time.sleep(5) 
            main() # Coba rekoneksi 
        except Exception as e: 
            print_debug(f"Error tak terduga: {e}") 
            time.sleep(5) 
 
if __name__ == "__main__": 
    main()