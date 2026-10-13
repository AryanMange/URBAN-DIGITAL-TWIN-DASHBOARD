# 🏙️ Urban Digital Twin Analytics — Mumbai Metropolitan Region

An end-to-end Big Data Analytics and IoT digital twin platform designed for real-time urban management. The system ingests continuous, multi-domain sensor telemetry across six municipal sectors in Mumbai, detects physical anomalies using statistical boundaries, forecasts grid and traffic loads using Meta Prophet, and renders an interactive command center with zero manual refresh required.

---

## 📌 Problem Statement & Overview

Modern smart cities generate heterogeneous streaming data from loop vehicle counters, air quality monitoring stations, electrical substations, municipal bus fleets, and weather arrays. Conventional approaches rely on static reports or decoupled business intelligence dashboards that only evaluate historical logs.

**Urban Digital Twin Analytics** solves this problem by maintaining a synchronized digital representation of the physical city. It tracks cross-domain interdependencies in real time (e.g., peak ambient temperatures driving electrical substation loads; roadway congestion directly worsening air quality and transit schedules).

---

## 🏛️ System Architecture

```text
                     URBAN DATA SOURCES
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
   Open-Meteo REST API    Simulated IoT        Physical Sensor
   (Live Mumbai Weather)  Telemetry Streams      Input Buffers
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                   STREAM INGESTION ENGINE
                   (realtime_collector.py)
                   Emits every 5 seconds
                              │
                              ▼
                    STREAM BUFFER CACHE
                   (data/realtime_feed.csv)
                              │
                              ▼
                   ANALYTICS & DIAGNOSTICS
                       (processor.py)
         ┌────────────────────┼────────────────────┐
         │                    │                    │
   Tukey IQR Anomaly    Meta Prophet 24h     Composite City
   Detection Engine       Forecasting         Health Index
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                   STREAMLIT COMMAND CENTER
                           (app.py)
         ┌────────────────────┼────────────────────┐
         │                    │                    │
   Live Status Indicators  Plotly Geospatial   7 Sector Drill-Down
     (● LIVE / 5s Poll)     Mumbai Mapbox           Panels
```

---

## 🌟 Key Features

* **Real-Time Cyber-Physical Mirroring:** Decoupled background telemetry ingestion emitting synchronized readings every 5 seconds.
* **Geospatial Zone Monitoring:** Live status mapping for 6 strategic Mumbai zones:
  * South Mumbai
  * Central Mumbai
  * Western Suburbs (Andheri)
  * Western Suburbs (Bandra)
  * Eastern Suburbs (Ghatkopar)
  * Navi Mumbai (Vashi)
* **Heterogeneous Domain Coverage:**
  * **Traffic Analytics:** Vehicle counts, velocity degradation, and congestion classification.
  * **Air Quality & Pollution:** AQI, $\text{PM}_{2.5}$, $\text{PM}_{10}$, $\text{CO}$, and $\text{NO}_2$.
  * **Energy Grid:** Substation power draw in Megawatts (MW) and peak demand trends.
  * **Public Transit:** Active municipal bus counts, schedule adherence, and delay SLAs.
  * **Infrastructure Telemetry:** Pavement conditions and traffic signal controller states.
  * **Ambient Weather:** Synchronized temperature and relative humidity telemetry.
* **Statistical Anomaly Detection:** Real-time flagging using Tukey's Interquartile Range (IQR) rule ($1.5 \times \text{IQR}$).
* **Predictive Analytics:** 24-hour horizon time-series forecasting for grid power demand and traffic congestion using Meta Prophet.
* **Incident Ledger:** Filterable active emergency feed highlighting hardware faults, grid overloads, and hazardous AQI levels.

---

## 🛠️ Technology Stack

| Layer | Technologies Used |
| :--- | :--- |
| **Language & Environment** | Python 3.10+, PowerShell / Command Prompt |
| **Data Processing & ETL** | pandas, NumPy |
| **Predictive Analytics** | Meta Prophet, scikit-learn |
| **Live Web Ingestion** | Requests (Open-Meteo REST API), Schedule |
| **Visualization & UI** | Streamlit, Plotly Express, Plotly Graph Objects |
| **Storage Architecture** | Rolling time-series CSV cache buffers (`data/`) |

---

## 📂 Project Structure

```text
URBAN DIGITAL TWIN DASHBOARD/
│
├── data/                             # Generated automatically
│   ├── sensor_data.csv               # Historical 5-day baseline telemetry
│   ├── realtime_feed.csv             # Rolling real-time streaming buffer
│   ├── processed_data.csv            # Cleaned telemetry with anomaly tags
│   ├── forecast_traffic.csv          # Prophet 24-hour traffic forecast
│   ├── forecast_energy.csv           # Prophet 24-hour power load forecast
│   └── active_alerts.csv             # Triggered incident ledger
│
├── app.py                            # Streamlit command center dashboard
├── data_gen.py                       # Historical baseline synthesizer
├── processor.py                      # Anomaly detection & Prophet forecasting
├── realtime_collector.py             # Background 5-second streaming daemon
├── requirements.txt                  # Python dependencies
├── run_twin.bat                      # Windows one-click automated launcher
└── README.md                         # Project documentation
```

---

## 🚀 Setup & Execution Guide

### Prerequisites
* Windows 10/11
* Python 3.10 to 3.12 installed with **"Add python.exe to PATH"** selected.

---

### Step 1: Environment Initialization

Open PowerShell in the project directory:

```powershell
# Allow script execution for the current session
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# Create virtual environment (one time only)
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Install requirements
pip install -r requirements.txt
```

---

### Step 2: Initialize Historical Baseline & Analytics

Generate baseline sensor records and train initial predictive models:

```powershell
python data_gen.py
python processor.py
```

---

### Step 3: Run the Live Digital Twin

The project uses a decoupled producer-consumer architecture requiring two concurrent processes:

#### Terminal 1 — Telemetry Stream Ingestion Engine
```powershell
.\venv\Scripts\Activate.ps1
python realtime_collector.py --interval 5
```
*(Leave this terminal open. It emits a fresh synchronized IoT frame batch every 5 seconds.)*

#### Terminal 2 — Command Center UI
Open a second terminal window in the same folder:
```powershell
.\venv\Scripts\Activate.ps1
streamlit run app.py
```
Streamlit will automatically launch `http://localhost:8501` in your default browser.

---

### ⚡ One-Click Windows Launch

Alternatively, launch both components automatically using the provided batch file:
1. Double-click `run_twin.bat` in the project root.
2. The script activates the virtual environment, starts the background collector, and launches the browser UI.

---

## 🔬 Mathematical & Diagnostic Foundations

### 1. Tukey's Interquartile Range (IQR) Anomaly Rule
To detect abnormal power consumption spikes, traffic congestion, and sensor telemetry faults without high computational overhead, the platform applies Tukey's IQR boundary condition:

$$\text{IQR} = Q_3 - Q_1$$

$$\text{Lower Bound} = Q_1 - 1.5 \times \text{IQR}, \quad \text{Upper Bound} = Q_3 + 1.5 \times \text{IQR}$$

Readings falling outside this interval are flagged as anomalies in `processed_data.csv` and populated into the active incident ledger.

### 2. Composite City Health Index
The high-level municipal status is tracked through a penalty-weighted index bounded between $0\%$ and $100\%$:

$$\text{Health Index} = 100 - (\text{Penalty}_{\text{traffic}} + \text{Penalty}_{\text{aqi}} + \text{Penalty}_{\text{transit}} + \text{Penalty}_{\text{hardware}})$$

Where:
* $\text{Penalty}_{\text{traffic}} = \left(\frac{\text{Traffic Density}}{100}\right) \times 35$
* $\text{Penalty}_{\text{aqi}} = \min\left(1, \frac{\text{AQI}}{300}\right) \times 35$
* $\text{Penalty}_{\text{transit}} = \min\left(1, \frac{\text{Bus Delay Mins}}{30}\right) \times 15$
* $\text{Penalty}_{\text{hardware}} = 15 \text{ if Signal Status is OFFLINE, else } 0$

---

## 🎓 Academic Defense & Viva Q&A Summary

* **Q: Why is this a Digital Twin rather than just a dashboard?**
  * **A:** Conventional dashboards present disconnected historical logs. A Digital Twin maintains synchronized cyber-physical state mirroring, models cross-domain physical relationships (traffic directly driving pollution and transit delays), and produces forward-looking predictive simulations.
* **Q: Where is the data sourced?**
  * **A:** Ambient weather is fetched from the **Open-Meteo REST API**. Municipal IoT data (loop counters, substation power meters, fleet GPS) is generated via a deterministic simulator calibrated to Mumbai's diurnal cycles and rush-hour dynamics.
* **Q: Why use Prophet for time-series forecasting?**
  * **A:** City telemetry exhibits pronounced diurnal periodicity (morning/evening rush periods, afternoon temperature and cooling load peaks). Meta Prophet models these cyclical patterns and trend changepoints with low computational latency suitable for localized operation.
* **Q: How would this scale to production?**
  * **A:** In production, the CSV buffer would be replaced with an **Apache Kafka** distributed message broker, persistence would migrate to a time-series database (e.g., **TimescaleDB**), and stream processing would be handled by **Apache Spark Streaming** or **Apache Flink**.

---

## 📜 License & Acknowledgments
Developed as a college mini-project in **Big Data Analytics & IoT Systems**. Built using open-source tools: Streamlit, Plotly, Meta Prophet, and Open-Meteo.