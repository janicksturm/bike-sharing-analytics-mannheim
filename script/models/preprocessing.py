import pandas as pd
import duckdb

from .metrics import calculate_station_occupancy_capacity

"""
This module contains functions for loading and preprocessing the bike-sharing data.
"""
def load_all_snapshots() -> pd.DataFrame:
    """Load all snapshot files and combine them into a single DataFrame with additional features."""
    dfs = duckdb.sql(
        " SELECT regexp_extract(filename, 'data_([0-9]{8}_[0-9]{6})', 1) AS snapshot_time, uid, CAST(lat AS FLOAT) AS lat, CAST(lng AS FLOAT) AS lng, name, number, bikes, bikes_available_to_rent, bike_racks, free_racks FROM read_parquet('data/raw/*.parquet');"
    ).to_df()

    dfs = features(dfs)
    return dfs

def features(df: pd.DataFrame) -> pd.DataFrame:
    """Add derived features to the DataFrame."""
    df = df.copy()

    df["total_capacity"] = df["bikes"] + df["free_racks"]

    df["occupancy_pct"] = calculate_station_occupancy_capacity(df)

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