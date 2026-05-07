import streamlit as st
import pandas as pd
import os
import json

RAW_DIR = "data/raw"
GEO_DIR = "data/geo"

# Load and combine all parquet snapshot files into one DataFrame
@st.cache_data(ttl=300)
def load_all_snapshots() -> pd.DataFrame:
    files = sorted(
        f for f in os.listdir(RAW_DIR) if f.endswith(".parquet")
    )
    dfs = []
    for f in files:
        df = pd.read_parquet(os.path.join(RAW_DIR, f))
        ts_str = f.replace("data_", "").replace(".parquet", "")
        df["snapshot_time"] = pd.to_datetime(ts_str, format="%Y%m%d_%H%M%S")
        df["snapshot_label"] = df["snapshot_time"].dt.strftime("%H:%M")
        dfs.append(df)
    all_df = pd.concat(dfs, ignore_index=True)
    
    # Ensure coordinates are numeric
    all_df["lat"] = all_df["lat"].astype(float)
    all_df["lng"] = all_df["lng"].astype(float)

    all_df["total_capacity"] = all_df["bikes"] + all_df["free_racks"]

    all_df["occupancy_pct"] = (
        all_df["bikes"] / all_df["total_capacity"].replace(0, pd.NA) * 100
    ).fillna(0).round(1)

    all_df["status"] = all_df["bikes"].apply(
        lambda b: "Empty" if b == 0 else ("Low" if b <= 2 else "Available")
    )
    return all_df

# Load latest GeoJSON file for map visualization
@st.cache_data(ttl=300)
def load_latest_geojson():
    path = os.path.join(GEO_DIR, "latest.geojson")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None