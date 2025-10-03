# IoT Network Website Implementation Using LoRa Point-to-Point (P2P)  
## Environmental Radiation Monitoring on a Radiation Portal Monitor  

This project is the implementation of a bachelor thesis by **Aryaguna Abi Rafdi Yasa** (UPN Veteran Jakarta, Electrical Engineering, 2025).  
The main objective is to design and implement a **LoRa Point-to-Point (P2P) wireless communication system** to support radiation monitoring using a **Radiation Portal Monitor (RPM)**, especially in areas with limited network infrastructure.  

The system connects a **Centralized Alarm System (CAS)** to a **Raspberry Pi-based gateway**, and presents monitoring data through a **near real-time web interface**.  

---

## 🔍 Background
- Nuclear and radioactive material security has become a global concern, with thousands of incidents recorded by the IAEA.  
- RPM (Radiation Portal Monitor) plays a vital role at borders/ports, but its effectiveness is limited by poor network infrastructure.  
- LoRa offers a reliable, energy-efficient, and long-range alternative communication method.  

---

## 🎯 Objectives
1. Design and implement a LoRa-based P2P communication system for long-range radiation monitoring.  
2. Develop a Raspberry Pi-based web monitoring system to display data in **real-time**.  
3. Evaluate system performance based on **RSSI, Latency, and Packet Loss**.  

---

## ⚙️ System Architecture
- **Radiation Portal Monitor (RPM)** detects radiation.  
- **CAS (Centralized Alarm System)** transmits data via RS-485.  
- **LoRa Node (Arduino Nano + RS485-TTL + E90-DTU LoRa Module)** sends data wirelessly.  
- **LoRa Gateway (Raspberry Pi + RS485-TTL + LoRa Module)** receives and stores data.  
- **Web Interface** displays monitoring results, graphs, and radiation alerts.  

### Workflow
RPM → CAS → LoRa Node → LoRa Gateway → Raspberry Pi → Database → Web Interface  

---

## 🛠️ Hardware
- **Raspberry Pi 4 Model B** (gateway + web server)  
- **Arduino Nano (ATmega328)**  
- **LoRa Module E90-DTU (900SL30)**  
- **RS485 to TTL Converter**  
- **LoRa Antenna (915 MHz, 3 dBi)**  
- **Radiation Portal Monitor (BRIN, Building 72)**  

---

## 💻 Software
- **Arduino IDE** (Arduino programming)  
- **Python & Flask / PHP** (Raspberry Pi backend web server)  
- **MySQL Database** (data storage)  
- **HTML, CSS, JavaScript** (frontend web monitoring)  

---

## 📊 Results
Field tests were carried out at 3 different locations with varying obstacles.  
- **Packet Loss**: up to 34.72% under worst-case conditions.  
- **Latency**: average < 1.5 seconds.  
- **RSSI**: within TIPHON standards (good to fair).  
- The system remained **stable** without failures, even in challenging environments.  

The web interface successfully displayed **near real-time monitoring** and generated alerts when radiation exceeded threshold values.  

---

## 🚀 How to Run
1. **Setup Arduino Nano + LoRa Node**  
   - Upload Arduino code using Arduino IDE.  
   - Connect to CAS via RS485.  

2. **Setup Raspberry Pi Gateway**  
   - Install Python + Flask/PHP + MySQL.  
   - Connect RS485 to LoRa Gateway.  
   - Run the web server.  

3. **Access Monitoring Website**  
   - Open a browser and access the Raspberry Pi IP address.  
   - The web app displays radiation status, graphs, and alarms.  

---

## 📚 References
- International Atomic Energy Agency (IAEA)  
- TIPHON Standards (Packet Loss, Delay, RSSI)  
- Previous research on LoRa & RPM  

---

## 👨‍💻 Author
**Aryaguna Abi Rafdi Yasa**  
- Faculty of Engineering, Electrical Engineering  
- Universitas Pembangunan Nasional Veteran Jakarta  
- Class of 2025  
