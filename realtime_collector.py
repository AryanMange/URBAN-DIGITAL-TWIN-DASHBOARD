"""
realtime_collector.py
---------------------
Real-Time Telemetry Stream Ingestion Engine for Urban Digital Twin.
Fetches ambient conditions and generates synchronized IoT frames across Mumbai zones.
Outputs: data/realtime_feed.csv
"""

import os
import sys
import time
import csv
import math
import random
import argparse
import requests
import pandas as pd
from datetime import datetime

OUTPUT_FILE = os.path.join("data", "realtime_feed.csv")
MAX_ROWS = 2500

ZONES = {
    "South Mumbai": {"lat": 18.9388, "lon": 72.8354, "base_traffic": 65, "base_energy": 5.2, "base_aqi": 110},
    "Central Mumbai": {"lat": 19.0178, "lon": 72.8478, "base_traffic": 70, "base_energy": 4.8, "base_aqi": 125},
    "Western Suburbs (Andheri)": {"lat": 19.1197, "lon": 72.8464, "base_traffic": 75, "base_energy": 6.1, "base_aqi": 140},
    "Western Suburbs (Bandra)": {"lat": 19.0596, "lon": 72.8295, "base_traffic": 68, "base_energy": 5.5, "base_aqi": 118},
    "Eastern Suburbs (Ghatkopar)": {"lat": 19.0860, "lon": 72.9090, "base_traffic": 62, "base_energy": 4.2, "base_aqi": 135},
    "Navi Mumbai (Vashi)": {"lat": 19.0771, "lon": 72.9986, "base_traffic": 50, "base_energy": 3.9, "base_aqi": 95},
}

FIELDNAMES = [
    "id", "timestamp", "city", "zone", "latitude", "longitude",
    "traffic_density", "vehicle_count", "average_speed", "congestion_level",
    "aqi", "pm25", "pm10", "co", "no2", "energy_consumption_mw",
    "temperature", "humidity", "bus_count", "bus_delay_mins",
    "road_condition", "traffic_signal_status", "data_source"
]

def fetch_live_weather():
    """Fetches live weather from Open-Meteo for Mumbai (No API key needed)."""
    try:
        url = "https://api.open-meteo.com/v1/forecast?latitude=19.0760&longitude=72.8777&current=temperature_2m,relative_humidity_2m"
        res = requests.get(url, timeout=3.5).json()
        curr = res.get("current", {})
        return float(curr.get("temperature_2m", 29.5)), float(curr.get("relative_humidity_2m", 72.0)), "LIVE_API_DATA"
    except Exception:
        # Fallback to diurnal synthetic model
        hr = datetime.now().hour
        t = 27.5 + 5.5 * math.sin((hr - 8) * math.pi / 12)
        return round(t, 1), 74.0, "SIMULATED_IoT_SENSOR_DATA"

def generate_telemetry_batch():
    live_temp, live_hum, source_type = fetch_live_weather()
    now_dt = datetime.now()
    now_str = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    hour = now_dt.hour
    is_rush = (8 <= hour <= 11) or (17 <= hour <= 21)
    rush_mult = 1.30 if is_rush else (0.50 if 1 <= hour <= 5 else 1.0)
    
    batch = []
    for zone_name, meta in ZONES.items():
        t_density = min(99.0, max(12.0, meta["base_traffic"] * rush_mult + random.uniform(-6.0, 7.0)))
        v_count = int(t_density * random.uniform(19.0, 23.0))
        speed = max(6.0, 64.0 - (t_density * 0.52) + random.uniform(-3.0, 3.0))
        
        # Correlated emissions and grid load
        aqi = max(40.0, meta["base_aqi"] * (t_density / 62.0) + random.uniform(-8.0, 8.0))
        energy = round(meta["base_energy"] * rush_mult + max(0.0, (live_temp - 28.0) * 0.15) + random.uniform(-0.2, 0.3), 2)
        b_delay = round(max(0.0, (t_density - 50.0) * 0.45 + random.uniform(-1.0, 3.0)), 1)
        
        # Signal status distribution
        sig_rand = random.random()
        sig_stat = "OFFLINE" if sig_rand < 0.04 else ("FLASHING_YELLOW" if sig_rand < 0.12 else "OPERATIONAL")
        
        batch.append({
            "id": f"frame_{int(time.time())}_{zone_name[:3]}",
            "timestamp": now_str,
            "city": "Mumbai",
            "zone": zone_name,
            "latitude": meta["lat"],
            "longitude": meta["lon"],
            "traffic_density": round(t_density, 1),
            "vehicle_count": v_count,
            "average_speed": round(speed, 1),
            "congestion_level": "CRITICAL" if t_density > 82 else ("HIGH" if t_density > 65 else "NORMAL"),
            "aqi": round(aqi, 0),
            "pm25": round(aqi * 0.42, 1),
            "pm10": round(aqi * 0.78, 1),
            "co": round(0.5 + (aqi * 0.012), 2),
            "no2": round(15.0 + (t_density * 0.45), 1),
            "energy_consumption_mw": energy,
            "temperature": live_temp,
            "humidity": live_hum,
            "bus_count": int(random.uniform(22, 45) * rush_mult),
            "bus_delay_mins": b_delay,
            "road_condition": "POOR" if random.random() < 0.15 else "GOOD",
            "traffic_signal_status": sig_stat,
            "data_source": source_type
        })
    return batch

def append_and_rotate(rows: list[dict]):
    os.makedirs("data", exist_ok=True)
    file_exists = os.path.exists(OUTPUT_FILE)
    
    with open(OUTPUT_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        for r in rows:
            writer.writerow(r)
            
    try:
        df = pd.read_csv(OUTPUT_FILE)
        if len(df) > MAX_ROWS:
            df.tail(MAX_ROWS).to_csv(OUTPUT_FILE, index=False)
    except Exception:
        pass

def main():
    parser = argparse.ArgumentParser(description="Urban Digital Twin Telemetry Collector")
    parser.add_argument("--interval", type=int, default=5, help="Seconds between streaming ticks (default: 5)")
    parser.add_argument("--once", action="store_true", help="Emit one telemetry frame batch and exit")
    args = parser.parse_args()

    print("[collector] Urban Digital Twin Streaming Daemon initialized.")
    print(f"[collector] Output: {OUTPUT_FILE} | Tick interval: {args.interval}s")
    print("[collector] Emitting synchronized cross-domain IoT readings... (Press Ctrl+C to stop)")

    while True:
        batch = generate_telemetry_batch()
        append_and_rotate(batch)
        ts = datetime.now().strftime("%H:%M:%S")
        print(f"[{ts}] Emitted {len(batch)} telemetry updates for Mumbai zones ({batch[0]['data_source']})")
        if args.once:
            break
        time.sleep(args.interval)

if __name__ == "__main__":
    main()