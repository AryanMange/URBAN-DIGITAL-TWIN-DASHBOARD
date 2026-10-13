"""
data_gen.py
-----------
Generates historical baseline IoT telemetry for the Urban Digital Twin (Mumbai).
Outputs: data/sensor_data.csv
"""

import os
import csv
import math
import random
from datetime import datetime, timedelta

random.seed(42)

ZONES = {
    "South Mumbai": {"lat": 18.9388, "lon": 72.8354, "base_traffic": 65, "base_energy": 5.2, "base_aqi": 110},
    "Central Mumbai": {"lat": 19.0178, "lon": 72.8478, "base_traffic": 70, "base_energy": 4.8, "base_aqi": 125},
    "Western Suburbs (Andheri)": {"lat": 19.1197, "lon": 72.8464, "base_traffic": 75, "base_energy": 6.1, "base_aqi": 140},
    "Western Suburbs (Bandra)": {"lat": 19.0596, "lon": 72.8295, "base_traffic": 68, "base_energy": 5.5, "base_aqi": 118},
    "Eastern Suburbs (Ghatkopar)": {"lat": 19.0860, "lon": 72.9090, "base_traffic": 62, "base_energy": 4.2, "base_aqi": 135},
    "Navi Mumbai (Vashi)": {"lat": 19.0771, "lon": 72.9986, "base_traffic": 50, "base_energy": 3.9, "base_aqi": 95},
}

SIGNAL_STATUSES = ["OPERATIONAL", "OPERATIONAL", "OPERATIONAL", "FLASHING_YELLOW", "OFFLINE"]
ROAD_CONDITIONS = ["GOOD", "GOOD", "MODERATE", "MODERATE", "POOR"]

def generate_historical_stream(days: int = 7, interval_mins: int = 30) -> list[dict]:
    rows = []
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    current_time = start_time
    row_id = 1

    while current_time <= end_time:
        hour = current_time.hour
        # Diurnal curves: Morning peak (8-11 AM) and Evening peak (5-9 PM)
        is_rush = (8 <= hour <= 11) or (17 <= hour <= 21)
        rush_multiplier = 1.35 if is_rush else (0.45 if 1 <= hour <= 5 else 1.0)
        temp_cycle = 27.0 + 6.0 * math.sin((hour - 8) * math.pi / 12) + random.uniform(-1.0, 1.0)

        for zone_name, meta in ZONES.items():
            # Domain Correlated Variables
            traffic_density = min(99.0, max(10.0, meta["base_traffic"] * rush_multiplier + random.uniform(-8.0, 8.0)))
            vehicle_count = int(traffic_density * random.uniform(18.0, 24.0))
            avg_speed = max(8.0, 65.0 - (traffic_density * 0.55) + random.uniform(-4.0, 4.0))
            
            # Higher traffic directly raises emissions
            aqi = max(35.0, meta["base_aqi"] * (traffic_density / 60.0) + random.uniform(-12.0, 12.0))
            pm25 = round(aqi * 0.42 + random.uniform(-5.0, 5.0), 1)
            pm10 = round(aqi * 0.78 + random.uniform(-8.0, 8.0), 1)
            co = round(0.5 + (aqi * 0.012) + random.uniform(-0.1, 0.2), 2)
            no2 = round(15.0 + (traffic_density * 0.45) + random.uniform(-3.0, 3.0), 1)

            # High temperature increases grid load (HVAC demand)
            temp_load_boost = max(0.0, (temp_cycle - 28.0) * 0.18)
            energy_consumption = round(meta["base_energy"] * (0.8 + 0.3 * rush_multiplier) + temp_load_boost + random.uniform(-0.3, 0.4), 2)

            bus_count = int(random.uniform(20, 45) * rush_multiplier)
            bus_delay = round(max(0.0, (traffic_density - 50.0) * 0.42 + random.uniform(-2.0, 4.0)), 1)
            humidity = round(max(40.0, min(95.0, 72.0 - (temp_cycle - 27.0) * 2.0 + random.uniform(-5.0, 5.0))), 1)

            # Injected anomalies (1.5% chance)
            if random.random() < 0.015:
                anomaly_type = random.choice(["TRAFFIC_JAM", "ENERGY_SPIKE", "POLLUTION_SURGE"])
                if anomaly_type == "TRAFFIC_JAM":
                    traffic_density = min(99.0, traffic_density * 1.45)
                    avg_speed = max(4.0, avg_speed * 0.35)
                elif anomaly_type == "ENERGY_SPIKE":
                    energy_consumption = round(energy_consumption * 1.7, 2)
                elif anomaly_type == "POLLUTION_SURGE":
                    aqi = aqi * 1.8
                    pm25 = pm25 * 1.9

            rows.append({
                "id": row_id,
                "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S"),
                "city": "Mumbai",
                "zone": zone_name,
                "latitude": meta["lat"],
                "longitude": meta["lon"],
                "traffic_density": round(traffic_density, 1),
                "vehicle_count": vehicle_count,
                "average_speed": round(avg_speed, 1),
                "congestion_level": "CRITICAL" if traffic_density > 82 else ("HIGH" if traffic_density > 65 else "NORMAL"),
                "aqi": round(aqi, 0),
                "pm25": pm25,
                "pm10": pm10,
                "co": co,
                "no2": no2,
                "energy_consumption_mw": energy_consumption,
                "temperature": round(temp_cycle, 1),
                "humidity": humidity,
                "bus_count": bus_count,
                "bus_delay_mins": bus_delay,
                "road_condition": random.choice(ROAD_CONDITIONS),
                "traffic_signal_status": random.choice(SIGNAL_STATUSES),
                "data_source": "HISTORICAL_BASELINE"
            })
            row_id += 1

        current_time += timedelta(minutes=interval_mins)

    return rows

def main():
    os.makedirs("data", exist_ok=True)
    out_path = os.path.join("data", "sensor_data.csv")
    print(f"[data_gen] Synthesizing continuous urban telemetry for Mumbai...")
    dataset = generate_historical_stream(days=5, interval_mins=30)
    
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(dataset[0].keys()))
        writer.writeheader()
        writer.writerows(dataset)
    print(f"[data_gen] Successfully generated {len(dataset)} telemetry frames -> {out_path}")

if __name__ == "__main__":
    main()