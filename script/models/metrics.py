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