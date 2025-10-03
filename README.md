# Implementasi Website Jaringan IoT Menggunakan LoRa Point-to-Point (P2P)  
## Pemantauan Radiasi Lingkungan pada Radiation Portal Monitor  

Proyek ini merupakan implementasi dari skripsi **Aryaguna Abi Rafdi Yasa** (UPN Veteran Jakarta, Teknik Elektro, 2025).  
Tujuan utama penelitian ini adalah membangun sistem komunikasi nirkabel berbasis **LoRa Point-to-Point (P2P)** untuk mendukung pemantauan radiasi menggunakan **Radiation Portal Monitor (RPM)**, khususnya di lokasi dengan keterbatasan infrastruktur jaringan.  

Sistem ini menghubungkan **Centralized Alarm System (CAS)** dengan **gateway berbasis Raspberry Pi**, kemudian menyajikan data pemantauan secara **near real-time** melalui antarmuka website.

---

## 🔍 Latar Belakang
- Keamanan material nuklir dan radioaktif menjadi isu global penting (IAEA mencatat ribuan kasus penyalahgunaan).  
- RPM (Radiation Portal Monitor) berfungsi mendeteksi radiasi di perbatasan/pelabuhan, namun keterbatasan jaringan konvensional membuat data sulit diteruskan secara cepat.  
- LoRa dipilih sebagai solusi komunikasi alternatif yang hemat energi, jangkauan jauh, dan andal.  

---

## 🎯 Tujuan
1. Mendesain dan mengimplementasikan komunikasi LoRa P2P untuk pemantauan radiasi jarak jauh.  
2. Mengembangkan website berbasis Raspberry Pi untuk monitoring data secara **real-time**.  
3. Mengevaluasi performa sistem berdasarkan **RSSI, Latency, dan Packet Loss**.  

---

## ⚙️ Arsitektur Sistem
- **Radiation Portal Monitor (RPM)** mendeteksi radiasi.  
- **CAS (Centralized Alarm System)** mengirim data ke **LoRa Node** melalui RS-485.  
- **LoRa Node (Arduino Nano + RS485-TTL + E90-DTU LoRa Module)** meneruskan data secara wireless.  
- **LoRa Gateway (Raspberry Pi + RS485-TTL + LoRa Module)** menerima data dan menyimpannya ke database.  
- **Website** menampilkan data monitoring, grafik, dan notifikasi alarm radiasi.  

### Flow
RPM → CAS → LoRa Node → LoRa Gateway → Raspberry Pi → Database → Website  

---

## 🛠️ Hardware yang Digunakan
- **Raspberry Pi 4 Model B** (server + gateway monitoring)  
- **Arduino Nano (ATmega328)**  
- **Modul LoRa E90-DTU (900SL30)**  
- **RS485 to TTL Converter**  
- **Antena LoRa (915 MHz, 3 dBi)**  
- **Radiation Portal Monitor (BRIN, Gedung 72)**  

---

## 💻 Software
- **Arduino IDE** (pemrograman Arduino Nano)  
- **Python & Flask / PHP (pada Raspberry Pi untuk backend web)**  
- **Database MySQL** (penyimpanan data RPM)  
- **HTML, CSS, JavaScript** (frontend website monitoring)  

---

## 📊 Hasil Pengujian
Pengujian dilakukan pada 3 lokasi berbeda dengan variasi halangan fisik.  
- **Packet Loss**: hingga 34,72% pada kondisi terburuk.  
- **Latency**: rata-rata < 1,5 detik.  
- **RSSI**: sesuai standar TIPHON dengan kategori baik hingga cukup.  
- Sistem tetap **stabil** tanpa kegagalan meski dalam kondisi lingkungan ekstrem.  

Website berhasil menampilkan data radiasi **near real-time** dan memberikan alarm jika melebihi ambang batas.  

---

## 🚀 Cara Menjalankan
1. **Setup Arduino Nano + LoRa Node**:  
   - Upload kode Arduino melalui Arduino IDE.  
   - Hubungkan ke CAS melalui RS485.  

2. **Setup Raspberry Pi Gateway**:  
   - Install Python + Flask/PHP + MySQL.  
   - Hubungkan RS485 ke LoRa Gateway.  
   - Jalankan server web.  

3. **Akses Website Monitoring**:  
   - Buka browser dan akses alamat IP Raspberry Pi.  
   - Website akan menampilkan status radiasi, grafik, dan alarm.  

---

## 📚 Referensi
- International Atomic Energy Agency (IAEA)  
- Standar TIPHON (Packet Loss, Delay, RSSI)  
- Penelitian terdahulu tentang LoRa & RPM  

---

## 👨‍💻 Author
**Aryaguna Abi Rafdi Yasa**  
- Fakultas Teknik, Prodi S1 Teknik Elektro  
- Universitas Pembangunan Nasional Veteran Jakarta  
- Tahun 2025  
