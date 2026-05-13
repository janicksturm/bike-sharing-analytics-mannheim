import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium

from script.view.view_utils import chart_layout
from script.view.data_loader import load_all_snapshots, load_latest_geojson

PLOTLY_TEMPLATE = "plotly_dark"
CHART_BG = "rgba(22,27,34,0)"
PAPER_BG = "rgba(22,27,34,0)"

# Page config
st.set_page_config(
    page_title="NextBike Mannheim · Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Background */
.stApp {
    background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
    color: #e6edf3;
}

/* KPI cards */
.kpi-card {
    background: linear-gradient(135deg, rgba(33,38,45,0.9), rgba(22,27,34,0.95));
    border: 1px solid rgba(48,54,61,0.7);
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
    backdrop-filter: blur(10px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    margin-bottom: 12px;
}
.kpi-card:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 30px rgba(0,0,0,0.4);
}
.kpi-label {
    font-size: 0.75rem;
    font-weight: 500;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #8b949e;
    margin-bottom: 6px;
}
.kpi-value {
    font-size: 2.2rem;
    font-weight: 700;
    line-height: 1;
}
.kpi-green  { color: #3fb950; }
.kpi-red    { color: #f85149; }
.kpi-blue   { color: #58a6ff; }
.kpi-orange { color: #d29922; }
.kpi-delta {
    font-size: 0.8rem;
    color: #8b949e;
    margin-top: 4px;
}

/* Section headers */
.section-header {
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    color: #8b949e;
    border-bottom: 1px solid rgba(48,54,61,0.6);
    padding-bottom: 6px;
    margin: 20px 0 12px;
}

/* Plotly chart containers */
.js-plotly-plot { border-radius: 12px; }

/* Hide Streamlit branding */
#MainMenu, footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# Load data
df_all = load_all_snapshots()

snapshots = sorted(df_all["snapshot_time"].unique())
latest_ts = snapshots[-1]
df_latest = df_all[df_all["snapshot_time"] == latest_ts].copy()

terminal_types = sorted(df_latest["terminal_type"].dropna().unique().tolist())


# Titel
st.markdown("""
<div style="padding: 8px 0 1px;">
    <h1 style="font-size:1.9rem; font-weight:700; color:#e6edf3; margin:0;">
        NextBike Mannheim
        <span style="font-size:1rem; font-weight:400; color:#8b949e;">Station Analytics Dashboard</span>
    </h1>
</div>
""", unsafe_allow_html=True)

# Snapshot selector for "single snapshot" views
snapshot_labels = {
    ts: pd.Timestamp(ts).strftime("%d.%m.%Y %H:%M") for ts in snapshots
}
selected_ts_label = st.selectbox(
    "Snapshot",
    options=list(snapshot_labels.values()),
    index=len(snapshot_labels) - 1,
)
selected_ts = [k for k, v in snapshot_labels.items() if v == selected_ts_label][0]
df_selected = df_all[df_all["snapshot_time"] == selected_ts].copy()


st.markdown('<div class="section-header">Status</div>', unsafe_allow_html=True)

# KPI row
total_bikes = int(df_selected["bikes"].sum())
total_available = int(df_selected["bikes_available_to_rent"].fillna(0).sum())
empty_stations = int((df_selected["bikes"] == 0).sum())
total_stations = len(df_selected)
avg_occupancy = df_selected["occupancy_pct"].mean()
total_free_racks = int(df_selected["free_racks"].sum())

# compare to previous snapshot if exists
prev_snapshots = [s for s in snapshots if s < pd.Timestamp(selected_ts)]
delta_bikes = ""
if prev_snapshots:
    df_prev = df_all[df_all["snapshot_time"] == prev_snapshots[-1]]
    prev_bikes = int(df_prev["bikes"].sum())
    diff = total_bikes - prev_bikes
    delta_bikes = f"{'▲' if diff >= 0 else '▼'} {abs(diff)} vs prev snapshot"

k1, k2, k3, k4 = st.columns(4)

with k1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Total Bikes</div>
        <div class="kpi-value kpi-blue">{total_bikes}</div>
        <div class="kpi-delta">{delta_bikes}</div>
    </div>""", unsafe_allow_html=True)

with k2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Available to Rent</div>
        <div class="kpi-value kpi-green">{total_available}</div>
        <div class="kpi-delta">across {total_stations} stations</div>
    </div>""", unsafe_allow_html=True)

with k3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Empty Stations</div>
        <div class="kpi-value kpi-red">{empty_stations}</div>
        <div class="kpi-delta">{empty_stations/total_stations*100:.0f}% of stations</div>
    </div>""", unsafe_allow_html=True)

with k4:
    color = "kpi-green" if avg_occupancy >= 50 else ("kpi-orange" if avg_occupancy >= 20 else "kpi-red")
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">Avg Occupancy</div>
        <div class="kpi-value {color}">{avg_occupancy:.1f}%</div>
        <div class="kpi-delta">{total_free_racks} free racks</div>
    </div>""", unsafe_allow_html=True)


# Map
st.markdown('<div class="section-header">Station Distribution</div>', unsafe_allow_html=True)

map_col, dist_col = st.columns([3, 2], gap="medium")

with map_col:
    center_lat = df_selected["lat"].mean()
    center_lng = df_selected["lng"].mean()

    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles=None,
    )

    folium.TileLayer(
        tiles="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
        attr="CartoDB · OpenStreetMap contributors",
        name="Dark Matter",
        max_zoom=20,
    ).add_to(m)

    for _, row in df_selected.iterrows():
        bikes = int(row["bikes"])
        free  = int(row["free_racks"])
        total = bikes + free

        if bikes == 0:
            color = "#f85149"
            icon_color = "red"
        elif bikes <= 2:
            color = "#d29922"
            icon_color = "orange"
        else:
            color = "#3fb950"
            icon_color = "green"

        occ = row["occupancy_pct"]

        rentable = int(row['bikes_available_to_rent']) if pd.notna(row['bikes_available_to_rent']) else 0
        popup_html = f"""
        <div style="font-family:Inter,sans-serif;min-width:180px;">
            <b style="font-size:1em;">{row['name']}</b><br>
            <hr style="margin:4px 0; border-color:#ccc;">
            <table style="font-size:0.88em; width:100%;">
                <tr><td>Bikes</td><td><b>{bikes}</b></td></tr>
                <tr><td>Rentable</td><td><b>{rentable}</b></td></tr>
                <tr><td>Free racks</td><td><b>{free}</b></td></tr>
                <tr><td>Occupancy</td><td><b>{occ:.0f}%</b></td></tr>
            </table>
        </div>
        """

        folium.CircleMarker(
            location=[row["lat"], row["lng"]],
            radius=5,
            color="#21262d",
            weight=1.2,
            fill_color=color,
            fill_opacity=0.85,
            popup=folium.Popup(popup_html, max_width=240),
            tooltip=f"{row['name']} · {bikes} bikes",
        ).add_to(m)

    st_folium(m, height=420, width="stretch")

with dist_col:
    # Status pie
    status_counts = df_selected["status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    color_map = {"Available": "#3fb950", "Low": "#d29922", "Empty": "#f85149"}

    fig_pie = go.Figure(go.Pie(
        labels=status_counts["Status"],
        values=status_counts["Count"],
        hole=0.55,
        marker=dict(
            colors=[color_map.get(s, "#58a6ff") for s in status_counts["Status"]],
            line=dict(color="#0d1117", width=2),
        ),
        textinfo="label+percent",
        textfont=dict(size=13, color="#e6edf3"),
    ))
    fig_pie.update_layout(
        title="Station Status",
        template=PLOTLY_TEMPLATE,
        paper_bgcolor=PAPER_BG,
        height=200,
        margin=dict(l=0, r=0, t=60, b=0),
        font=dict(family="Inter", color="#8b949e"),
        legend=dict(orientation="h", yanchor="top", y=1.2, xanchor="left", x=1.0),
        showlegend=True,
    )
    st.plotly_chart(fig_pie, width="stretch")

# Station Ranking
st.markdown('<div class="section-header"> Station Ranking</div>', unsafe_allow_html=True)

top10 = df_selected.nlargest(10, "bikes")[["name", "bikes", "free_racks", "occupancy_pct"]].copy()
top10 = top10.sort_values("bikes")
fig_top = go.Figure(go.Bar(
    x=top10["bikes"], y=top10["name"],
    orientation="h",
    text=[f"{b} bikes" for b in top10["bikes"]],
    textposition="inside",
    textfont=dict(size=11),
))
fig_top.update_layout(title="Top 10 Stations by Bike Count")
chart_layout(fig_top, height=340)
st.plotly_chart(fig_top, width="stretch")


# Footer
st.markdown(f"""
<style>

.footer {{
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;

    height: 60px;

    background: #0d1117;
    border-top: 1px solid #30363d;

    display: flex;
    flex-direction: column;

    align-items: center;
    justify-content: center;

    text-align: center;

    color: #8b949e;
    font-size: 0.75rem;

    z-index: 999999;
}}

.footer-title {{
    font-weight: 600;
}}

.footer-sub {{
    font-size: 0.7rem;
    opacity: 0.8;
}}

.block-container {{
    padding-bottom: 80px;
}}

</style>

<div class="footer">
    <div class="footer-title">NextBike Dashboard · Live Monitoring</div>
    <div class="footer-sub">Snapshots: {len(snapshots)} · Stations: {df_latest['uid'].nunique()}</div>
</div>
""", unsafe_allow_html=True)