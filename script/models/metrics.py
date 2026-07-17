import pandas as pd

"""
This module contains functions for calculating various metrics from the bike-sharing data.
"""
def calculate_empty_rate(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate the percentage of time each station is empty."""
    return (
        df.groupby("uid")["bikes"]
        .apply(lambda x: (x == 0).mean())
        .reset_index(name="empty_rate")
    )

# We want to calculate how full each bike station is. 
# First, we find out the total number of spaces by adding the number of bikes currently there and the number of free racks. 
# Then, we calculate the percentage of those spaces that are occupied by bikes. 
# If there are no spaces available (total capacity is zero), we avoid dividing by zero 
# by only calculating the percentage where the total capacity is greater than zero. 
def calculate_station_occupancy_capacity(df: pd.DataFrame) -> pd.Series:
    _capacity = df["total_capacity"].astype(float)
    return (
        (df["bikes"] / _capacity.where(_capacity > 0) * 100)
        .fillna(0)
        .round(1)
    )