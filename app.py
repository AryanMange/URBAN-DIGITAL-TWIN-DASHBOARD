"""
app.py
------
Urban Digital Twin Analytics — Real-Time Smart City Monitoring & Command Center
"""

import os
import glob
import subprocess
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ── Page Configuration ────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Urban Digital Twin Analytics — Mumbai",
    page_icon="🏙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Command Center Dark/Clean CSS ─────────────────────────────────────────────

st.markdown("""
<style>
    .main { background-color: #0e1117; }
    [data-testid="metric-container"] {
        background-color: #1a1f2c;
        border: 1px solid #2d3748;
        border-radius: 8px;
        padding: 12px 16px;
        color: #ffffff;
    }
    .header-strip {
        background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 50%, #415a77 100%);
        color: white;
        padding: 20px 24px;
        border-radius: 10px;
        border: 1px solid #415a77;
        margin-bottom: 20px;
    }
    .live-badge {
        background-color: #ef4444;
        color: white;
        padding: 4px 10px;
        border-radius: 12px;
        font-weight: 700;
        font-size: 0.82rem;
        display: inline-block;
        animation: blinker 1.5s linear infinite;
    }
    @keyframes blinker {
        50% { opacity: 0.3; }
    }
    .section-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #64b5f6;
        border-left: 4px solid #1976d2;
        padding-left: 10px;
        margin: 18px 0 12px 0;
    }
</style>
""", unsafe_allow_html=True)

# ── Data Loading & State Management ──────────────────────────────────────────

PROCESSED_CSV   = os.path.join("data", "processed_data.csv")
REALTIME_FEED   = os.path.join("data", "realtime_feed.csv")
RAW_SENSOR_CSV  = os.path.join("data", "sensor_data.csv")
ALERTS_CSV      = os.path.join("data", "active_alerts.csv")
FORECAST_ENERGY = os.path.join("data", "forecast_energy.csv")
FORECAST_TRAFFIC= os.path.join("data", "forecast_traffic.csv")

def load_data():
    """Reads latest streaming telemetry frame."""
    if os.path.exists(REALTIME_FEED):
        df = pd.read_csv(REALTIME_FEED)
    elif os.path.exists(PROCESSED_CSV):
        df = pd.read_csv(PROCESSED_CSV)
    elif os.path.exists(RAW_SENSOR_CSV):
        df = pd.read_csv(RAW_SENSOR_CSV)
    else:
        st.error("No telemetry stream located. Click 'Initialize City Baseline' in the sidebar.")
        st.stop()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df

# ── Sidebar Controls ──────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## 🏙️ Twin Controls")
    st.markdown("*Mumbai Metropolitan Operations Center*")
    st.divider()

    st.markdown("### ⚡ Telemetry Operations")
    col_sb1, col_sb2 = st.columns(2)
    with col_sb1:
        if st.button("Generate Baseline", use_container_width=True):
            with st.spinner("Synthesizing 7-day city history..."):
                subprocess.run(["python", "data_gen.py"], check=True)
                subprocess.run(["python", "processor.py"], check=True)
            st.rerun()
    with col_sb2:
        if st.button("Run Analytics", use_container_width=True):
            with st.spinner("Executing Anomaly Models..."):
                subprocess.run(["python", "processor.py"], check=True)
            st.rerun()

    st.divider()
    st.markdown("### 🔄 Streaming Refresh")
    auto_refresh = st.toggle("Auto-Refresh Telemetry", value=True)
    refresh_rate = st.slider("Poll Interval (seconds)", min_value=3, max_value=30, value=5)

    st.divider()
    st.markdown("### 📍 Geospatial Filter")
    df_full = load_data()
    all_zones = ["All Zones"] + sorted(df_full["zone"].unique().tolist())
    selected_zone = st.selectbox("Select Urban Zone", options=all_zones, index=0)

    st.caption(f"Stream State: Active | Polling: {refresh_rate}s")

# ── Filter View ───────────────────────────────────────────────────────────────

if selected_zone != "All Zones":
    df_view = df_full[df_full["zone"] == selected_zone].copy()
else:
    df_view = df_full.copy()

latest_df = df_view.sort_values("timestamp").groupby("zone").last().reset_index()

# ── Header Strip ──────────────────────────────────────────────────────────────

latest_source = latest_df["data_source"].iloc[0] if "data_source" in latest_df.columns else "SIMULATED_IoT"
now_str = datetime.now().strftime("%H:%M:%S")

st.markdown(f"""
<div class="header-strip">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1 style="margin:0; font-size: 1.8rem;">🏙️ URBAN DIGITAL TWIN ANALYTICS</h1>
            <p style="margin: 4px 0 0 0; color: #90caf9;">Real-Time Smart City Monitoring, Diagnostics & Predictive Operations — Mumbai</p>
        </div>
        <div style="text-align: right;">
            <span class="live-badge">● LIVE</span>
            <div style="font-size: 0.85rem; margin-top: 6px; color: #cfd8dc;">Source: <b>{latest_source}</b></div>
            <div style="font-size: 0.8rem; color: #90a4ae;">Last Frame: <b>{now_str}</b></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── KPI Cards ─────────────────────────────────────────────────────────────────

kpi_traffic = round(latest_df["traffic_density"].mean(), 1)
kpi_aqi     = int(latest_df["aqi"].mean())
kpi_energy  = round(latest_df["energy_consumption_mw"].sum(), 2)
kpi_buses   = int(latest_df["bus_count"].sum())
kpi_temp    = round(latest_df["temperature"].mean(), 1)
kpi_health  = round(latest_df["city_health_score"].mean(), 1) if "city_health_score" in latest_df.columns else 88.5

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("🚗 Avg Traffic", f"{kpi_traffic}%", delta=f"{'High' if kpi_traffic > 70 else 'Normal'}", delta_color="inverse")
c2.metric("🌫️ City AQI", f"{kpi_aqi}", delta=f"{'Unhealthy' if kpi_aqi > 150 else 'Moderate'}", delta_color="inverse")
c3.metric("⚡ Power Demand", f"{kpi_energy} MW", delta="Substation Load")
c4.metric("🚌 Active Fleet", f"{kpi_buses} Buses", delta=f"Avg Delay: {round(latest_df['bus_delay_mins'].mean(),1)}m", delta_color="inverse")
c5.metric("🌡️ Ambient Temp", f"{kpi_temp} °C", delta=f"Humidity: {int(latest_df['humidity'].mean())}%")
c6.metric("🏙️ City Health Index", f"{kpi_health}%", delta=f"{'Warning' if kpi_health < 75 else 'Optimal'}")

st.divider()

# ── Dashboard Tabs ────────────────────────────────────────────────────────────

tabs = st.tabs([
    "1. Overview & Geospatial Map",
    "2. Traffic Analytics",
    "3. Pollution Analytics",
    "4. Energy Grid",
    "5. Public Transport",
    "6. Infrastructure Status",
    "7. Alerts & Diagnostics"
])

# ── TAB 1: Overview ───────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-title">🗺️ Geospatial Sensor Status — Mumbai Metropolitan Region</div>', unsafe_allow_html=True)
    
    # Map marker severity
    def determine_status(r):
        if r["traffic_density"] > 80 or r["aqi"] > 180 or r["traffic_signal_status"] == "OFFLINE":
            return "Critical"
        if r["traffic_density"] > 65 or r["aqi"] > 125 or r["bus_delay_mins"] > 10:
            return "Warning"
        return "Normal"

    map_df = latest_df.copy()
    map_df["Twin_Status"] = map_df.apply(determine_status, axis=1)

    color_discrete_map = {"Normal": "#10b981", "Warning": "#f59e0b", "Critical": "#ef4444"}

    # Multi-version compatibility (Plotly v6+ uses scatter_map, v5 uses scatter_mapbox)
    map_func = getattr(px, "scatter_map", None) or getattr(px, "scatter_mapbox", None)
    style_param = "map_style" if hasattr(px, "scatter_map") else "mapbox_style"

    map_kwargs = {
        "data_frame": map_df,
        "lat": "latitude",
        "lon": "longitude",
        "color": "Twin_Status",
        "color_discrete_map": color_discrete_map,
        "size": "vehicle_count",
        "size_max": 22,
        "hover_name": "zone",
        "hover_data": {
            "traffic_density": True,
            "aqi": True,
            "energy_consumption_mw": True,
            "bus_delay_mins": True,
            "traffic_signal_status": True,
            "latitude": False,
            "longitude": False
        },
        "zoom": 10.2,
        "center": {"lat": 19.0600, "lon": 72.8800},
        "height": 480,
        style_param: "carto-positron"
    }

    fig_map = map_func(**map_kwargs)
    fig_map.update_layout(margin=dict(t=0, b=0, l=0, r=0))
    st.plotly_chart(fig_map, use_container_width=True)

    col_sub1, col_sub2 = st.columns(2)
    with col_sub1:
        st.markdown('<div class="section-title">📊 Zone-by-Zone Operational Load</div>', unsafe_allow_html=True)
        fig_bar = px.bar(
            latest_df, x="zone", y=["traffic_density", "energy_consumption_mw"],
            barmode="group", labels={"value": "Level / MW", "variable": "Sensor Metric"},
            color_discrete_sequence=["#3b82f6", "#10b981"]
        )
        fig_bar.update_layout(height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_sub2:
        st.markdown('<div class="section-title">⚠️ Real-Time Anomaly Distribution</div>', unsafe_allow_html=True)
        status_counts = map_df["Twin_Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_pie = px.pie(status_counts, names="Status", values="Count", color="Status", color_discrete_map=color_discrete_map, hole=0.5)
        fig_pie.update_layout(height=280, margin=dict(t=10, b=10))
        st.plotly_chart(fig_pie, use_container_width=True)

# ── TAB 2: Traffic Analytics ──────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-title">🚗 Traffic Density & Velocity Flow Dynamics</div>', unsafe_allow_html=True)
    t_col1, t_col2 = st.columns([2, 1])
    with t_col1:
        # Time-series trend
        time_traffic = df_view.tail(120).copy()
        fig_traffic = px.line(time_traffic, x="timestamp", y="traffic_density", color="zone",
                              title="Rolling Traffic Density (%)", markers=False)
        fig_traffic.update_layout(height=340, margin=dict(t=30, b=10))
        st.plotly_chart(fig_traffic, use_container_width=True)
    with t_col2:
        # Diagnostic Analytics: Speed vs Traffic Density
        fig_diag = px.scatter(df_view.tail(150), x="traffic_density", y="average_speed", color="congestion_level",
                              title="Speed Degradation Correlation", color_discrete_map={"CRITICAL": "#ef4444", "HIGH": "#f59e0b", "NORMAL": "#10b981"})
        fig_diag.update_layout(height=340, margin=dict(t=30, b=10))
        st.plotly_chart(fig_diag, use_container_width=True)

    # Traffic Prophet Forecast
    if os.path.exists(FORECAST_TRAFFIC):
        st.markdown('<div class="section-title">📈 Predictive Analytics: 24-Hour Traffic Density Forecast (Prophet)</div>', unsafe_allow_html=True)
        f_df = pd.read_csv(FORECAST_TRAFFIC)
        f_df["ds"] = pd.to_datetime(f_df["ds"])
        fig_tf = go.Figure()
        hist = f_df[~f_df["is_forecast"]]
        pred = f_df[f_df["is_forecast"]]
        fig_tf.add_trace(go.Scatter(x=hist["ds"].tail(48), y=hist["yhat"].tail(48), name="Observed Density", line=dict(color="#3b82f6")))
        fig_tf.add_trace(go.Scatter(x=pred["ds"], y=pred["yhat"], name="Prophet Forecast", line=dict(color="#f59e0b", dash="dash")))
        fig_tf.add_trace(go.Scatter(x=pd.concat([pred["ds"], pred["ds"][::-1]]),
                                    y=pd.concat([pred["yhat_upper"], pred["yhat_lower"][::-1]]),
                                    fill="toself", fillcolor="rgba(245, 158, 11, 0.15)", line=dict(color="rgba(255,255,255,0)"), name="85% Confidence"))
        fig_tf.update_layout(height=260, margin=dict(t=10, b=10), yaxis_title="Congestion Density (%)")
        st.plotly_chart(fig_tf, use_container_width=True)

# ── TAB 3: Pollution Analytics ────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-title">🌫️ Air Quality & Particulate Matter Analytics</div>', unsafe_allow_html=True)
    p1, p2 = st.columns(2)
    with p1:
        fig_aqi_bar = px.bar(latest_df, x="zone", y="aqi", color="aqi",
                             color_continuous_scale="Reds", title="Current AQI by Sector")
        fig_aqi_bar.update_layout(height=320, margin=dict(t=30, b=10))
        st.plotly_chart(fig_aqi_bar, use_container_width=True)
    with p2:
        fig_pm = px.scatter(latest_df, x="pm25", y="pm10", size="co", color="zone",
                            title="Particulate Dispersion (PM2.5 vs PM10, Size=CO)", hover_name="zone")
        fig_pm.update_layout(height=320, margin=dict(t=30, b=10))
        st.plotly_chart(fig_pm, use_container_width=True)

# ── TAB 4: Energy Grid ────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown('<div class="section-title">⚡ Substation Demand & Peak Load Analytics</div>', unsafe_allow_html=True)
    e1, e2 = st.columns([2, 1])
    with e1:
        fig_energy = px.line(df_view.tail(120), x="timestamp", y="energy_consumption_mw", color="zone",
                             title="Real-Time Grid Load (Megawatts)")
        fig_energy.update_layout(height=320, margin=dict(t=30, b=10))
        st.plotly_chart(fig_energy, use_container_width=True)
    with e2:
        tot_energy = latest_df.groupby("zone")["energy_consumption_mw"].sum().reset_index()
        fig_epie = px.pie(tot_energy, names="zone", values="energy_consumption_mw", title="Power Distribution", hole=0.4)
        fig_epie.update_layout(height=320, margin=dict(t=30, b=10))
        st.plotly_chart(fig_epie, use_container_width=True)

    if os.path.exists(FORECAST_ENERGY):
        st.markdown('<div class="section-title">📈 24-Hour Substation Demand Forecast (Prophet Model)</div>', unsafe_allow_html=True)
        ef_df = pd.read_csv(FORECAST_ENERGY)
        ef_df["ds"] = pd.to_datetime(ef_df["ds"])
        fig_ef = go.Figure()
        fig_ef.add_trace(go.Scatter(x=ef_df[~ef_df["is_forecast"]]["ds"].tail(48), y=ef_df[~ef_df["is_forecast"]]["yhat"].tail(48), name="Actual Demand", line=dict(color="#10b981")))
        fig_ef.add_trace(go.Scatter(x=ef_df[ef_df["is_forecast"]]["ds"], y=ef_df[ef_df["is_forecast"]]["yhat"], name="Prophet Forecast", line=dict(color="#6366f1", dash="dash")))
        fig_ef.update_layout(height=260, margin=dict(t=10, b=10), yaxis_title="Load (MW)")
        st.plotly_chart(fig_ef, use_container_width=True)

# ── TAB 5: Public Transport ───────────────────────────────────────────────────
with tabs[4]:
    st.markdown('<div class="section-title">🚌 Municipal Transit & Fleet Schedule Adherence</div>', unsafe_allow_html=True)
    col_pt1, col_pt2 = st.columns(2)
    with col_pt1:
        fig_delay = px.bar(latest_df, x="zone", y="bus_delay_mins", color="bus_delay_mins",
                           color_continuous_scale="thermal", title="Average Bus Schedule Delay (Minutes)")
        fig_delay.add_hline(y=15.0, line_dash="dot", line_color="red", annotation_text="Critical SLA (15 min)")
        fig_delay.update_layout(height=320, margin=dict(t=30, b=10))
        st.plotly_chart(fig_delay, use_container_width=True)
    with col_pt2:
        fig_fleet = px.bar(latest_df, x="zone", y="bus_count", title="Active Fleet Density per Sector", color_discrete_sequence=["#8b5cf6"])
        fig_fleet.update_layout(height=320, margin=dict(t=30, b=10))
        st.plotly_chart(fig_fleet, use_container_width=True)

# ── TAB 6: Infrastructure ─────────────────────────────────────────────────────
with tabs[5]:
    st.markdown('<div class="section-title">🛠️ Physical Infrastructure & Traffic Controller Status</div>', unsafe_allow_html=True)
    i1, i2 = st.columns(2)
    with i1:
        sig_data = latest_df["traffic_signal_status"].value_counts().reset_index()
        sig_data.columns = ["Controller State", "Count"]
        fig_sig = px.pie(sig_data, names="Controller State", values="Count", title="Signal Controller Reliability",
                         color="Controller State", color_discrete_map={"OPERATIONAL": "#10b981", "FLASHING_YELLOW": "#f59e0b", "OFFLINE": "#ef4444"})
        fig_sig.update_layout(height=300, margin=dict(t=30, b=10))
        st.plotly_chart(fig_sig, use_container_width=True)
    with i2:
        road_data = latest_df["road_condition"].value_counts().reset_index()
        road_data.columns = ["Pavement State", "Count"]
        fig_road = px.bar(road_data, x="Pavement State", y="Count", title="Road Pavement Monitoring", color="Pavement State")
        fig_road.update_layout(height=300, margin=dict(t=30, b=10))
        st.plotly_chart(fig_road, use_container_width=True)

# ── TAB 7: Alerts & Diagnostics ───────────────────────────────────────────────
with tabs[6]:
    st.markdown('<div class="section-title">🚨 Active Incidents & Diagnostics Rule Base</div>', unsafe_allow_html=True)
    if os.path.exists(ALERTS_CSV):
        alerts_data = pd.read_csv(ALERTS_CSV)
        if len(alerts_data) > 0:
            def style_alert(val):
                if val == "CRITICAL":
                    return "background-color: #fee2e2; color: #991b1b; font-weight: bold;"
                return "background-color: #fef3c7; color: #92400e; font-weight: bold;"
            
           # Multi-version compatibility (pandas >= 2.1 uses map, older versions use applymap)
            styler_func = getattr(alerts_data.style, "map", None) or getattr(alerts_data.style, "applymap")
            
            st.dataframe(
                styler_func(style_alert, subset=["severity"]),
                use_container_width=True,
                height=320
            )
        else:
            st.success("✅ All urban subsystems operating within nominal thresholds. No active anomalies.")
    else:
        st.info("Run processor.py to scan for physical anomalies.")

# ── Footer ────────────────────────────────────────────────────────────────────

st.markdown("""
<div style='text-align:center; color:#607d8b; font-size:0.85rem; padding: 24px 0 10px 0;'>
    Urban Digital Twin Analytics Platform  |  Big Data IoT Stream Processing Architecture<br>
    Continuous Telemetry Engine · Tukey IQR Anomaly Diagnostics · Meta Prophet 24h Forecasting
</div>
""", unsafe_allow_html=True)

# ── Auto-Refresh Trigger Loop ─────────────────────────────────────────────────

if auto_refresh:
    import time
    time.sleep(refresh_rate)
    st.rerun()