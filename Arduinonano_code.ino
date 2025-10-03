#include <SoftwareSerial.h> 
 
// --- Definisi Pin --- 
#define RE_PIN 5  // Pin RE (Receive Enable) pada modul RS485 
#define DE_PIN 4  // Pin DE (Driver Enable) pada modul RS485 
const byte LORA_RX_PIN = 2; // Pin RX SoftwareSerial (terhubung ke TX LoRa) 
const byte LORA_TX_PIN = 3; // Pin TX SoftwareSerial (terhubung ke RX LoRa) 
 
// --- Parameter Komunikasi --- 
const long BAUD_RATE = 9600; 
const unsigned long RS485_DELAY = 5; // Jeda (ms) untuk stabilisasi mode RS485 
const int BUFFER_SIZE = 250; 
 
// --- Buffer Data --- 
char pcBuffer[BUFFER_SIZE];   // Buffer untuk data dari PC 
byte pcCount = 0; 
char piBuffer[BUFFER_SIZE];   // Buffer untuk data dari Raspberry Pi 
byte piCount = 0; 
 
// Inisialisasi SoftwareSerial untuk komunikasi dengan modul LoRa 
SoftwareSerial LoRaSerial(LORA_RX_PIN, LORA_TX_PIN); 
 
// Variabel untuk RSSI. Nilai 0 digunakan sebagai placeholder. 
// Dalam sistem nyata, nilai ini harus didapat dari modul LoRa. 
byte dummy_rssi_byte = 0; 
 
// --- Fungsi untuk Mengatur Mode RS485 --- 
// 'transmit' = true untuk mode kirim, false untuk mode terima 
void setRS485Mode(bool transmit) { 
  // Untuk modul MAX485: 
  // Transmit -> RE=HIGH, DE=HIGH 
  // Receive  -> RE=LOW,  DE=LOW 
 
 
 
 
 
  // (Pastikan wiring Anda sesuai dengan logika ini) 
  digitalWrite(RE_PIN, transmit); 
  digitalWrite(DE_PIN, transmit); 
  delay(RS485_DELAY); 
} 
 
// --- Fungsi Setup (dijalankan sekali saat startup) --- 
void setup() { 
  pinMode(RE_PIN, OUTPUT); 
  pinMode(DE_PIN, OUTPUT); 
   
  setRS485Mode(false); // Mulai dalam mode Terima 
 
  Serial.begin(BAUD_RATE);       // Komunikasi serial dengan PC 
  LoRaSerial.begin(BAUD_RATE);   // Komunikasi serial dengan LoRa 
   
  delay(1500); 
  Serial.println("--- Nano Forwarder Siap ---"); 
} 
 
// --- Loop Utama (dijalankan terus-menerus) --- 
void loop() { 
  // 1. Cek data dari Raspberry Pi (via LoRaSerial) 
  setRS485Mode(false); // Pastikan dalam mode Terima 
  if (LoRaSerial.available()) { 
    char c = LoRaSerial.read(); 
    if (c == '\n') { 
      if (piCount > 0) { 
        piBuffer[piCount] = '\0'; // Jadikan string 
        // Jika perintahnya "get_data", teruskan ke PC 
        if (strcmp(piBuffer, "get_data") == 0) { 
          Serial.println("get_data"); 
          Serial.flush(); 
        } 
      } 
      piCount = 0; // Reset buffer 
    } else if (isprint(c) && piCount < BUFFER_SIZE - 1) { 
      piBuffer[piCount++] = c; 
    } 
  } 
 
  // 2. Cek data dari PC (via Serial) 
  if (Serial.available()) { 
    char c = Serial.read(); 
    if (c == '\n') { 
      if (pcCount > 0) { 
        pcBuffer[pcCount] = '\0'; // Jadikan string 
 
 
 
 
 
        // Jika data dari PC adalah CHUNK data, teruskan ke Pi 
        if (strncmp(pcBuffer, "CHUNK:1:", 8) == 0) { 
          setRS485Mode(true); // Ganti ke mode Kirim 
           
          LoRaSerial.print(pcBuffer);        // Kirim payload data 
          LoRaSerial.write(dummy_rssi_byte); // Tambahkan byte RSSI (placeholder) 
          LoRaSerial.println();              // Kirim newline sebagai penutup 
          LoRaSerial.flush(); 
           
          delay(100); // Jeda singkat setelah kirim 
          setRS485Mode(false); // Kembali ke mode Terima 
        } 
      } 
      pcCount = 0; // Reset buffer 
    } else if (isprint(c) && pcCount < BUFFER_SIZE - 1) { 
      pcBuffer[pcCount++] = c; 
    } 
  } 
}