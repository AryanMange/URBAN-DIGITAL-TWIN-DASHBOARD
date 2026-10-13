"""
processor.py
------------
Real-Time Analytics & Anomaly Detection Engine for Urban Digital Twin.
Performs ETL, Interquartile Range (IQR) Anomaly Detection, and Prophet Forecasting.

Outputs:
  data/processed_data.csv
  data/forecast_energy.csv
  data/forecast_traffic.csv
  data/active_alerts.csv
"""

import os
import time
import numpy as np
import pandas as pd
import warnings
warnings.filterwarnings("ignore")

RAW_HISTORICAL = os.path.join("data", "sensor_data.csv")
REALTIME_FEED  = os.path.join("data", "realtime_feed.csv")
OUTPUT_CSV     = os.path.join("data", "processed_data.csv")
FORECAST_ENERGY= os.path.join("data", "forecast_energy.csv")
FORECAST_TRAFFIC= os.path.join("data", "forecast_traffic.csv")
ALERTS_CSV     = os.path.join("data", "active_alerts.csv")

def load_combined_telemetry() -> pd.DataFrame:
    frames = []
    if os.path.exists(RAW_HISTORICAL):
        frames.append(pd.read_csv(RAW_HISTORICAL))
    if os.path.exists(REALTIME_FEED):
        frames.append(pd.read_csv(REALTIME_FEED))
    
    if not frames:
        raise FileNotFoundError("No sensor data found. Run data_gen.py or realtime_collector.py first.")
    
    df = pd.concat(frames, ignore_index=True)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.drop_duplicates(subset=["timestamp", "zone"]).sort_values("timestamp")
    return df

def detect_iqr_anomalies(df: pd.DataFrame, column: str, multiplier: float = 1.5) -> pd.Series:
    """Statistical Anomaly Detection using Tukey's Interquartile Range (IQR)."""
    q1 = df[column].quantile(0.25)
    q3 = df[column].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - multiplier * iqr
    upper = q3 + multiplier * iqr
    return (df[column] < lower) | (df[column] > upper)

def evaluate_infrastructure_alerts(df: pd.DataFrame) -> pd.DataFrame:
    """Identifies threshold violations across domains."""
    alerts = []
    latest_per_zone = df.sort_values("timestamp").groupby("zone").last().reset_index()

    for _, r in latest_per_zone.iterrows():
        # Traffic Thresholds
        if r["traffic_density"] >= 85:
            alerts.append({"timestamp": r["timestamp"], "zone": r["zone"], "domain": "Traffic",
                           "severity": "CRITICAL", "message": f"Severe Gridlock: Density at {r['traffic_density']}%"})
        elif r["traffic_density"] >= 75:
            alerts.append({"timestamp": r["timestamp"], "zone": r["zone"], "domain": "Traffic",
                           "severity": "WARNING", "message": f"Congestion buildup: Speed degraded to {r['average_speed']} km/h"})

        # Pollution Thresholds
        if r["aqi"] >= 200:
            alerts.append({"timestamp": r["timestamp"], "zone": r["zone"], "domain": "Pollution",
                           "severity": "CRITICAL", "message": f"Hazardous Air Quality: AQI at {int(r['aqi'])}"})
        elif r["aqi"] >= 140:
            alerts.append({"timestamp": r["timestamp"], "zone": r["zone"], "domain": "Pollution",
                           "severity": "WARNING", "message": f"Unhealthy Air Quality: PM2.5 elevated ({r['pm25']} µg/m³)"})

        # Energy Anomalies
        if r.get("energy_anomaly", False):
            alerts.append({"timestamp": r["timestamp"], "zone": r["zone"], "domain": "Energy",
                           "severity": "WARNING", "message": f"Abnormal Substation Surge: Load at {r['energy_consumption_mw']} MW"})

        # Infrastructure Hardware
        if r["traffic_signal_status"] == "OFFLINE":
            alerts.append({"timestamp": r["timestamp"], "zone": r["zone"], "domain": "Infrastructure",
                           "severity": "CRITICAL", "message": "Traffic Signal Hardware Failure: Controller Offline"})
        
        # Public Transport Delay
        if r["bus_delay_mins"] >= 15.0:
            alerts.append({"timestamp": r["timestamp"], "zone": r["zone"], "domain": "Transit",
                           "severity": "WARNING", "message": f"Bus Route Delays Exceeding 15m (Current: {r['bus_delay_mins']}m)"})

    return pd.DataFrame(alerts)

def run_prophet_forecasting(df: pd.DataFrame, target_col: str, out_file: str, periods: int = 24):
    """Generates 24-period future forecast using Prophet."""
    try:
        from prophet import Prophet
        daily = df[["timestamp", target_col]].rename(columns={"timestamp": "ds", target_col: "y"})
        daily = daily.resample("1h", on="ds").mean().dropna().reset_index()

        if len(daily) < 15:
            print(f"[processor] Insufficient points for {target_col} forecast.")
            return

        model = Prophet(daily_seasonality=True, weekly_seasonality=False, interval_width=0.85)
        model.fit(daily)
        future = model.make_future_dataframe(periods=periods, freq="h")
        forecast = model.predict(future)

        res = forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].copy()
        res["is_forecast"] = res["ds"] > daily["ds"].max()
        res.to_csv(out_file, index=False)
        print(f"[processor] Exported Prophet forecast -> {out_file}")
    except Exception as e:
        print(f"[processor] Forecasting skipped for {target_col}: {e}")

def main():
    print("[processor] Commencing Urban Digital Twin Data Analytics Pipeline...")
    t0 = time.time()
    df = load_combined_telemetry()

    # Anomaly Detection via IQR
    df["traffic_anomaly"] = detect_iqr_anomalies(df, "traffic_density")
    df["energy_anomaly"] = detect_iqr_anomalies(df, "energy_consumption_mw")
    df["aqi_anomaly"] = detect_iqr_anomalies(df, "aqi")

    # City Health Score (0 - 100%)
    # Penalty-based composite index
    traffic_penalty = (df["traffic_density"] / 100.0) * 35.0
    aqi_penalty = (df["aqi"] / 300.0).clip(0, 1) * 35.0
    delay_penalty = (df["bus_delay_mins"] / 30.0).clip(0, 1) * 15.0
    sig_penalty = (df["traffic_signal_status"] == "OFFLINE").astype(int) * 15.0

    df["city_health_score"] = (100.0 - (traffic_penalty + aqi_penalty + delay_penalty + sig_penalty)).clip(0, 100).round(1)

    # Save processed base
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"[processor] Cleaned & processed {len(df)} records -> {OUTPUT_CSV}")

    # Generate Alerts
    alerts_df = evaluate_infrastructure_alerts(df)
    alerts_df.to_csv(ALERTS_CSV, index=False)
    print(f"[processor] Active incidents identified: {len(alerts_df)} -> {ALERTS_CSV}")

    # Run Predictive Analytics
    run_prophet_forecasting(df, "energy_consumption_mw", FORECAST_ENERGY)
    run_prophet_forecasting(df, "traffic_density", FORECAST_TRAFFIC)

    print(f"[processor] Pipeline executed successfully in {round(time.time() - t0, 2)}s\n")

if __name__ == "__main__":
    main()