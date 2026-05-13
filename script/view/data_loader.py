import streamlit as st
import pandas as pd
import os
import json
from models.preprocessing import load_all_snapshots

RAW_DIR = "data/raw"
GEO_DIR = "data/geo"

# Load and combine all parquet snapshot files into one DataFrame
@st.cache_data(ttl=300)
def load_all_snapshots() -> pd.DataFrame:
    return load_all_snapshots()

# Load latest GeoJSON file for map visualization
@st.cache_data(ttl=300)
def load_latest_geojson():
    path = os.path.join(GEO_DIR, "latest.geojson")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return None