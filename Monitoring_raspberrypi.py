 
from flask import Flask, render_template_string 
import sqlite3 
 
# --- Konfigurasi --- 
DB_FILE = "/home/pi/Documents/final/monitoring_data.db" # Path ke file database 
SQLite 
REFRESH_INTERVAL = 1 # Interval auto-refresh halaman web (detik) 
 
# --- Ambang Batas Aman untuk Sensor B1 dan B2 --- 
B1_MEAN = 1250.0 
B2_MEAN = 2093.0 
B1_MIN = B1_MEAN * 0.75 
B1_MAX = B1_MEAN * 1.25 
B2_MIN = B2_MEAN * 0.66 
B2_MAX = B2_MEAN * 1.29 
 
app = Flask(__name__) # Inisialisasi aplikasi Flask 
 
# --- Template HTML untuk Web Dashboard --- 
 
 
 
 
 
# Menggunakan sintaks Jinja2 (contoh: {{ variabel }}) untuk menyisipkan data 
dinamis dari Python 
HTML_TEMPLATE = """ 
<!DOCTYPE html> 
<html lang="id"> 
<head> 
  <meta charset="UTF-8"> 
  <meta http-equiv="refresh" content="{{ refresh_interval }}"> 
  <title>Dashboard Monitoring v5</title> 
  <style> 
    body { font-family: Arial, sans-serif; padding: 20px; background-color: 
#f9f9f9; } 
    h1 { text-align: center; } 
    .status-box { padding: 20px; margin: 20px auto; text-align: center; font
size: 28px; font-weight: bold; border-radius: 10px; width: 400px; color: #333; } 
    .status-aman { background-color: #d4edda; } 
    .status-bahaya { background-color: #f8d7da; } 
    .notif { text-align: center; font-size: 18px; margin-bottom: 20px; } 
    table { width: 100%; border-collapse: collapse; margin-top: 20px; } 
    th, td { border: 1px solid #ccc; padding: 8px; text-align: center; } 
    th { background-color: #f2f2f2; } 
    .ok { background-color: #e2f7e2; } 
    .error { background-color: #fde2e2; } 
  </style> 
</head> 
<body> 
  <h1>Data Monitoring (Refresh Otomatis Setiap {{ refresh_interval }} 
detik)</h1> 
 
  <div class="status-box {{ 'status-aman' if status_global == 'AMAN' else 
'status-bahaya' }}"> 
      STATUS: {{ status_global }} 
  </div> 
 
  {% if notif_text %} 
  <div class="notif">{{ notif_text }}</div> 
  {% endif %} 
 
  <table> 
      <thead> 
          <tr> 
              <th>Timestamp</th> <th>Lokasi</th> <th>Siklus</th> <th>Pilar</th> 
              <th>B1</th> <th>B2</th> <th>L1</th> <th>L2</th> 
              <th>RSSI (dBm)</th> <th>Latency (s)</th> <th>Loss</th> <th>Status 
Loss</th> 
          </tr> 
      </thead> 
      <tbody> 
          {% for row in rows %} 
          {% set b1_aman = (b1_min <= row['b1'] <= b1_max) %} 
          {% set b2_aman = (b2_min <= row['b2'] <= b2_max) %} 
          {% set koneksi_aman = (row['status_loss'] == 'OK') %} 
          {% set aman_total = koneksi_aman and b1_aman and b2_aman %} 
          <tr class="{{ 'ok' if aman_total else 'error' }}"> 
              <td>{{ row['timestamp'] }}</td> <td>{{ row['location'] }}</td> 
              <td>{{ row['pi_cycle'] }}</td> <td>{{ row['pilar'] }}</td> 
              <td>{{ row['b1'] }}</td> <td>{{ row['b2'] }}</td> 
              <td>{{ "%.2f"|format(row['l1']) }}</td> <td>{{ 
"%.2f"|format(row['l2']) }}</td> 
              <td>{{ "%.2f"|format(row['rssi_dbm']) }}</td> <td>{{ 
"%.3f"|format(row['latency']) }}</td> 
              <td>{{ row['loss'] }}</td> <td>{{ row['status_loss'] }}</td> 
          </tr> 
          {% endfor %} 
      </tbody> 
  </table> 
</body> 
</html> 
""" 
 
@app.route("/") 
def index(): 
    """Menangani request ke URL utama, mengambil data, dan me-render template 
HTML.""" 
 
 
 
 
 
    conn = sqlite3.connect(DB_FILE) 
    conn.row_factory = sqlite3.Row  # Mengakses kolom berdasarkan nama 
    cursor = conn.cursor() 
    # Mengambil 10 data terakhir untuk ditampilkan 
    cursor.execute("SELECT * FROM monitoring ORDER BY id DESC LIMIT 10") 
    rows = cursor.fetchall() 
    conn.close() 
 
    status_global = "AMAN" 
    notif_text = "" 
 
    if rows: 
        # Cek status hanya berdasarkan data paling baru dari siklus terakhir 
        latest_cycle = rows[0]["pi_cycle"] 
        related_rows = [row for row in rows if row["pi_cycle"] == latest_cycle] 
 
        for row in related_rows: 
            # Jika ada status loss selain "OK", langsung set BAHAYA 
            if row["status_loss"] != "OK": 
                status_global = "BAHAYA" 
                notif_text = f"BAHAYA: Pilar {row['pilar']} mengalami 
'{row['status_loss']}'!" 
                break 
            # Jika nilai B1 di luar ambang batas 
            if not (B1_MIN <= row["b1"] <= B1_MAX): 
                status_global = "BAHAYA" 
                notif_text = f"BAHAYA: Nilai B1 ({row['b1']}) pada Pilar 
{row['pilar']} di luar batas!" 
                break 
            # Jika nilai B2 di luar ambang batas 
            if not (B2_MIN <= row["b2"] <= B2_MAX): 
                status_global = "BAHAYA" 
                notif_text = f"BAHAYA: Nilai B2 ({row['b2']}) pada Pilar 
{row['pilar']} di luar batas!" 
                break 
     
    # Render template HTML dan kirim data dinamis 
    return render_template_string( 
        HTML_TEMPLATE, 
        rows=rows, refresh_interval=REFRESH_INTERVAL, 
        b1_min=B1_MIN, b1_max=B1_MAX, b2_min=B2_MIN, b2_max=B2_MAX, 
        status_global=status_global, notif_text=notif_text 
    ) 
 
if __name__ == "__main__": 
    # Menjalankan server Flask yang dapat diakses dari jaringan 
    app.run(host="0.0.0.0", port=5000, debug=False) 