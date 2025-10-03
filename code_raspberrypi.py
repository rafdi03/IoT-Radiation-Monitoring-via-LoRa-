# Final_Web_Fix_Debug.py - Versi Final untuk Akuisisi Data via LoRa-RS485 
 
import serial 
import time 
import os 
import sqlite3 
import csv 
from datetime import datetime 
from time import monotonic as timer_monotonic 
 
# --- Konfigurasi Serial & Sistem --- 
SERIAL_PORT = "/dev/serial0"  # Port serial hardware UART di Raspberry Pi 
(terhubung ke converter RS485) 
BAUD_RATE = 9600              # Baud rate komunikasi, harus sama dengan Arduino 
REQUEST_INTERVAL = 5          # Jeda waktu (detik) antar pengiriman permintaan 
data ke Nano 
RESPONSE_TIMEOUT = 7.0        # Waktu maksimal (detik) menunggu balasan lengkap 
dari Nano 
BYTE_READ_TIMEOUT = 0.2       # Timeout untuk membaca satu byte dari port serial 
RS485_SWITCH_DELAY = 0.01     # Jeda singkat setelah mengubah mode 
Transmit/Receive RS485 
RS485_PRE_TX_DELAY = 0.02     # Jeda sebelum memulai transmisi via RS485 
RS485_POST_TX_DELAY = 0.05    # Jeda setelah selesai transmisi via RS485 
RS485_POST_RX_MODE_DELAY = 0.02 # Jeda setelah beralih ke mode Receive 
RSSI_OFFSET = 164             # Nilai offset untuk konversi byte RSSI mentah 
dari modul LoRa ke dBm (contoh: rssi_mentah - 164) 
EXPECTED_DATA_FIELDS = 9      # Jumlah field data yang diharapkan dalam payload 
dari PC 
DB_FILE = "/home/pi/Documents/final/monitoring_data.db" # Path absolut file 
database SQLite 
CSV_FILE = "/home/pi/Documents/final/data_final.csv"     # Path absolut file log 
CSV 
CURRENT_LOCATION = "A"        # Identifier untuk lokasi Raspberry Pi saat ini 
 
# --- Setup GPIO untuk Kontrol RE/DE pada RS485 --- 
# Menggunakan gpiozero (lebih modern) jika ada, jika tidak, kembali ke RPi.GPIO 
try: 
    from gpiozero import OutputDevice 
    RE_PIN, DE_PIN = 17, 27  # Pin GPIO untuk RE (Receive Enable) dan DE (Driver 
Enable) 
    # RE aktif LOW (initial_value=False), DE aktif HIGH (initial_value=False) 
    re_pin_gpiozero = OutputDevice(RE_PIN, active_high=False, 
initial_value=False) 
    de_pin_gpiozero = OutputDevice(DE_PIN, active_high=True, 
initial_value=False) 
    use_gpiozero = True 
except ImportError: 
    import RPi.GPIO as GPIO 
    RE_PIN, DE_PIN = 17, 27 
    GPIO.setmode(GPIO.BCM) 
    GPIO.setup(RE_PIN, GPIO.OUT, initial=GPIO.LOW) 
    GPIO.setup(DE_PIN, GPIO.OUT, initial=GPIO.LOW) 
    use_gpiozero = False 
 
# --- Fungsi Setup Database --- 
def setup_database(): 
    """Memastikan direktori database ada dan membuat tabel 'monitoring' jika 
belum ada.""" 
    os.makedirs(os.path.dirname(DB_FILE), exist_ok=True) 
    conn = sqlite3.connect(DB_FILE) 
    cursor = conn.cursor() 
    cursor.execute('''CREATE TABLE IF NOT EXISTS monitoring ( 
 
 
 
 
 
        id INTEGER PRIMARY KEY AUTOINCREMENT, 
        timestamp TEXT, location TEXT, pi_cycle INTEGER, pilar INTEGER, 
        b1 INTEGER, b2 INTEGER, l1 REAL, l2 REAL, 
        rssi_dbm REAL, latency REAL, loss INTEGER, status_loss TEXT 
    )''') 
    conn.commit() 
    conn.close() 
 
# --- Fungsi Tambah Data ke CSV --- 
def append_to_csv(row): 
    """Menambahkan baris data baru ke file CSV, membuat header jika file 
baru.""" 
    file_exists = os.path.isfile(CSV_FILE) 
    with open(CSV_FILE, 'a', newline='') as csvfile: 
        writer = csv.writer(csvfile) 
        if not file_exists: 
            writer.writerow(["timestamp", "location", "pi_cycle", "pilar", "b1", 
"b2", "l1", "l2", "rssi_dbm", "latency", "loss", "status_loss"]) 
        writer.writerow(row) 
 
# --- Fungsi Kontrol Mode RS485 --- 
def set_rs485_mode(transmit): 
    """Mengatur transceiver RS485 ke mode Transmit atau Receive.""" 
    if use_gpiozero: 
        # Transmit: RE off (LOW), DE on (HIGH). Receive: RE on (HIGH), DE off 
(LOW). 
        re_pin_gpiozero.off() if transmit else re_pin_gpiozero.on() 
        de_pin_gpiozero.on() if transmit else de_pin_gpiozero.off() 
    else: 
        # Asumsi RE aktif LOW, DE aktif HIGH. 
        GPIO.output(RE_PIN, GPIO.HIGH if transmit else GPIO.LOW) 
        GPIO.output(DE_PIN, GPIO.HIGH if transmit else GPIO.LOW) 
    time.sleep(RS485_SWITCH_DELAY) 
 
# --- Fungsi Simpan Data ke Database & CSV --- 
def insert_to_database(timestamp, location, pi_cycle, rpm1, rpm2, rssi_dbm, 
latency, loss, status_loss): 
    """Memasukkan data yang telah diproses ke database SQLite dan file CSV.""" 
    conn = sqlite3.connect(DB_FILE) 
    cursor = conn.cursor() 
 
    for pilar, rpm in zip([1, 2], [rpm1, rpm2]): 
        row = (timestamp, location, pi_cycle, pilar, 
               rpm['B1'], rpm['B2'], rpm['L1'], rpm['L2'], 
               rssi_dbm, latency, loss, status_loss) 
        cursor.execute('''INSERT INTO monitoring ( 
            timestamp, location, pi_cycle, pilar, b1, b2, l1, l2, 
            rssi_dbm, latency, loss, status_loss) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', row) 
        append_to_csv(row) 
 
    conn.commit() 
    conn.close() 
 
# --- Fungsi Parsing Data --- 
def parse_sensor_data(data_fields_list): 
    """Mem-parsing list field data dari PC menjadi dictionary untuk setiap 
pilar.""" 
    try: 
        # Format data: timestamp,B1p1,B2p1,L1p1,L2p1,B1p2,B2p2,L1p2,L2p2 
        return ( 
            {"B1": int(data_fields_list[1]), "B2": int(data_fields_list[2]), 
"L1": float(data_fields_list[3]), "L2": float(data_fields_list[4])}, 
            {"B1": int(data_fields_list[5]), "B2": int(data_fields_list[6]), 
"L1": float(data_fields_list[7]), "L2": float(data_fields_list[8])} 
        ) 
    except (ValueError, IndexError) as e: 
        print(f"[ERROR] Gagal mem-parsing data sensor: {e}") 
        return None, None 
 
# --- Fungsi Utama --- 
def main(): 
    setup_database() 
    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, Timeout=BYTE_READ_TIMEOUT) 
 
 
 
 
 
    set_rs485_mode(False)  # Mulai dalam mode Receive 
    time.sleep(0.1) 
    ser.reset_input_buffer() 
    pi_cycle_counter = 0 
 
    while True: 
        print("-" * 50) 
        pi_cycle_counter += 1 
        timestamp_req = datetime.now().isoformat(timespec='milliseconds') 
        print(f"[{timestamp_req}] Mengirim permintaan (Siklus 
{pi_cycle_counter})") 
 
        # --- Kirim Permintaan ke Arduino Nano --- 
        set_rs485_mode(True) 
        time.sleep(RS485_PRE_TX_DELAY) 
        ser.write(b"get_data\n") 
        ser.flush() 
        time.sleep(RS485_POST_TX_DELAY) 
        set_rs485_mode(False) 
        time.sleep(RS485_POST_RX_MODE_DELAY) 
 
        # --- Terima Balasan dari Arduino Nano --- 
        start_time = timer_monotonic() 
        buffer = bytearray() 
        complete = False 
 
        while timer_monotonic() - start_time < RESPONSE_TIMEOUT: 
            byte = ser.read(1) 
            if byte: 
                buffer.extend(byte) 
                if byte == b'\n': 
                    complete = True 
                    break 
         
        latency = round(timer_monotonic() - start_time, 3) 
 
        # --- Tangani jika Timeout atau Balasan Tidak Lengkap --- 
        if not complete: 
            print("[PERINGATAN] Timeout, balasan tidak lengkap!") 
            status_loss = "Timeout" 
            insert_to_database(timestamp_req, CURRENT_LOCATION, 
pi_cycle_counter, 
                               {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                               {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                               0.0, latency, 1, status_loss) 
            time.sleep(REQUEST_INTERVAL) 
            continue 
 
        # --- Tangani jika Balasan Terlalu Pendek --- 
        if len(buffer) < 6: 
            print(f"[PERINGATAN] Balasan terlalu pendek: {len(buffer)} bytes") 
            status_loss = "Short" 
            insert_to_database(timestamp_req, CURRENT_LOCATION, 
pi_cycle_counter, 
                               {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                               {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                               0.0, latency, 1, status_loss) 
            time.sleep(REQUEST_INTERVAL) 
            continue 
 
        # --- Ekstrak RSSI dan Payload --- 
        try: 
            # Asumsi 3 byte terakhir adalah [RSSI_BYTE, '\r', '\n'] 
            rssi_raw = buffer[-3]  
            rssi_dbm = float(rssi_raw - RSSI_OFFSET) 
            payload = buffer[:-3].decode('utf-8', errors='ignore').strip() 
            print(f"[DEBUG] Payload: {payload}") 
            print(f"[DEBUG] RSSI Mentah: {rssi_raw} -> {rssi_dbm:.2f} dBm") 
        except (IndexError, UnicodeDecodeError) as e: 
            print(f"[ERROR] Gagal decode payload atau ekstrak RSSI: {e}") 
            continue 
 
        # --- Proses Payload --- 
        if "CHUNK:1:" in payload: 
 
 
 
 
 
            data_part = payload.split("CHUNK:1:")[-1] 
            data_fields = data_part.split(',') 
            print(f"[DEBUG] Field data: {data_fields}") 
 
            if len(data_fields) == EXPECTED_DATA_FIELDS: 
                pilar1_data, pilar2_data = parse_sensor_data(data_fields) 
                if pilar1_data and pilar2_data: 
                    status_loss = "OK" 
                    insert_to_database(timestamp_req, CURRENT_LOCATION, 
pi_cycle_counter, 
                                       pilar1_data, pilar2_data, rssi_dbm, 
latency, 0, status_loss) 
                    print("[INFO] Data berhasil disimpan ke database dan CSV.") 
                else: 
                    print("[PERINGATAN] Gagal mem-parsing field data sensor.") 
            else: 
                print(f"[PERINGATAN] Jumlah field tidak cocok: 
{len(data_fields)} dari {EXPECTED_DATA_FIELDS} yang diharapkan.") 
                status_loss = "Mismatch" 
                insert_to_database(timestamp_req, CURRENT_LOCATION, 
pi_cycle_counter, 
                                   {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                                   {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                                   rssi_dbm, latency, 1, status_loss) 
        else: 
            print(f"[PERINGATAN] Format payload tidak sesuai. 'CHUNK:1:' tidak 
ditemukan.") 
            status_loss = "Invalid" 
            insert_to_database(timestamp_req, CURRENT_LOCATION, 
pi_cycle_counter, 
                               {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                               {'B1': 0, 'B2': 0, 'L1': 0.0, 'L2': 0.0}, 
                               rssi_dbm, latency, 1, status_loss) 
 
        time.sleep(REQUEST_INTERVAL) 
 
if __name__ == "__main__": 
    try: 
        main() 
    except KeyboardInterrupt: 
        print("\n[INFO] Script dihentikan oleh pengguna (Ctrl+C).") 
    except Exception as e: 
        print(f"[FATAL] Terjadi error yang tidak ditangani: {e}")