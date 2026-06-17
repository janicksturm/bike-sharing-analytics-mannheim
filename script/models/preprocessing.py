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

    if not files:
        raise FileNotFoundError(f"No .parquet files found in '{RAW_DIR}'. Run the data pipeline first.")

    dfs = []
    for f in files:
        df = pd.read_parquet(os.path.join(RAW_DIR, f))
        ts_str = f.replace("data_", "").replace(".parquet", "")
        df["snapshot_time"] = pd.to_datetime(ts_str, format="%Y%m%d_%H%M%S")
        df["snapshot_label"] = df["snapshot_time"].dt.strftime("%H:%M")
        dfs.append(df)
    all_dfs = pd.concat(dfs, ignore_index=True)

    # Sort by uid + time so that groupby-diff() produces correct deltas
    all_dfs = all_dfs.sort_values(["uid", "snapshot_time"]).reset_index(drop=True)

    all_dfs = remove_columns(all_dfs)
    all_dfs = features(all_dfs)

    return all_dfs

def features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features to the DataFrame."""
    df = df.copy()

    # lat/lng are stored as str in the Parquet source; convert explicitly
    df["lat"] = df["lat"].astype(float)
    df["lng"] = df["lng"].astype(float)

    df["total_capacity"] = df["bikes"] + df["free_racks"]

    # We want to calculate how full each bike station is. 
    # First, we find out the total number of spaces by adding the number of bikes currently there and the number of free racks. 
    # Then, we calculate the percentage of those spaces that are occupied by bikes. 
    # If there are no spaces available (total capacity is zero), we avoid dividing by zero 
    # by only calculating the percentage where the total capacity is greater than zero. 
    _capacity = df["total_capacity"].astype(float)
    df["occupancy_pct"] = (
        (df["bikes"] / _capacity.where(_capacity > 0) * 100)
        .fillna(0)
        .round(1)
    )

    # We want to categorize the bike availability.
    # If there are no bikes available, we label it as "Empty". 
    # If there are 1 or 2 bikes available, we label it as "Low". 
    # If there are more than 2 bikes available, we label it as "Available".
    df["status"] = df["bikes"].apply(
        lambda b: "Empty" if b == 0 else ("Low" if b <= 2 else "Available")
    )

    # We want to capture the change in bike availability at each station over time.
    # We calculate the difference in the number of bikes at each station between consecutive snapshots.
    # A negative difference (more bikes taken out) indicates higher demand, while a positive difference (more bikes returned) indicates lower demand. 
    df["bike_delta"] = df.groupby("uid")["bikes"].diff()

    # To create a demand score, we take the negative of the bike delta. 
    # This way, a higher demand (more bikes taken out) will result in a higher demand score, 
    # while a lower demand (more bikes returned) will result in a lower demand score.
    df["demand_score"] = -df["bike_delta"]

    return df

def remove_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove columns that are not needed for modeling."""
    df = df.copy()

    df = df.drop(["spot", "booked_bikes", "active_place", "terminal_type", "bike_numbers", "bike_types", "place_type", "bike", "rack_locks", "maintenance"], axis=1)

    return df