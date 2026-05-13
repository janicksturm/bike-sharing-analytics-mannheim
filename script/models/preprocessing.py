import os
import pandas as pd

RAW_DIR = "data/raw"

"""
This module contains functions for loading and preprocessing the bike-sharing data.
"""
def load_all_snapshots() -> pd.DataFrame:
    """Load all snapshot files and combine them into a single DataFrame with additional features."""
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
    all_dfs = pd.concat(dfs, ignore_index=True)
    
    all_dfs = features(all_dfs)
    
    return all_dfs

def features(df : pd.DataFrame) -> pd.DataFrame:
    """Add derived features to the DataFrame."""

    # Ensure coordinates are numeric
    df["lat"] = df["lat"].astype(float)
    df["lng"] = df["lng"].astype(float)

    df["total_capacity"] = df["bikes"] + df["free_racks"]

    df["occupancy_pct"] = (
        df["bikes"] / df["total_capacity"].replace(0, pd.NA) * 100
    ).fillna(0).round(1)

    df["status"] = df["bikes"].apply(
        lambda b: "Empty" if b == 0 else ("Low" if b <= 2 else "Available")
    )

    df["bike_delta"] = (
        df.groupby("uid")["bikes"].diff()
    )

    df["demand_score"] = -df["bike_delta"]

    return df