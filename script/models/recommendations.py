import numpy as np
import pandas as pd
from .utils import haversine


def _normalize(series: pd.Series) -> pd.Series:
    """Min-max normalize a Series to [0, 1].

    When all values are equal (max == min), returns 0.5 for every entry
    so that the factor contributes a neutral middle value.
    """
    min_val = series.min()
    max_val = series.max()
    if max_val == min_val:
        return pd.Series(0.5, index=series.index)
    return (series - min_val) / (max_val - min_val)


def score_stations_for_user(latest_data: pd.DataFrame, empty_rates: pd.DataFrame, user_lat: float, user_lng: float, top_n: int = 5) -> pd.DataFrame:
    """Rank all stations relative to the user's GPS position.

    The recommendation score combines:
    - Current bike availability (higher = better)
    - Historical reliability via empty rate (lower = better)
    - Walking distance to user (closer = better)
    - Recent demand trend (positive = bikes returning = better)
    """
    if latest_data.empty:
        return pd.DataFrame()

    candidates = latest_data.merge(empty_rates, on="uid", how="left")
    candidates["empty_rate"] = candidates["empty_rate"].fillna(0)

    # Compute distance from user to each station
    candidates["distance_meters"] = candidates.apply(
        lambda row: haversine(user_lat, user_lng, row["lat"], row["lng"]),
        axis=1,
    )

    # Only consider stations that currently have at least 1 bike
    candidates = candidates[candidates["bikes"] >= 1].copy()

    if candidates.empty:
        return pd.DataFrame()

    # Use demand_score as trend indicator (negative demand_score = bikes returning = good)
    candidates["demand_trend"] = -candidates["demand_score"].fillna(0)

    # Normalize all factors to [0, 1] so weights reflect true importance
    # Weights: bikes 35%, reliability 25%, proximity 25%, trend 15%
    candidates["recommendation_score"] = (
        _normalize(candidates["bikes"]) * 0.35
        + (1 - _normalize(candidates["empty_rate"])) * 0.25
        + (1 - _normalize(candidates["distance_meters"])) * 0.25
        + _normalize(candidates["demand_trend"]) * 0.15
    )

    candidates = candidates.sort_values("recommendation_score", ascending=False)

    #print(candidates.head(15)[["name", "bikes", "recommendation_score"]])

    return candidates.head(top_n).reset_index(drop=True)