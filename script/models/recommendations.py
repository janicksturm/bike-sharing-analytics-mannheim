import numpy as np
import pandas as pd
from .utils import haversine


def best_possible_station(latest_station_data: pd.DataFrame, neighbor_stations: pd.DataFrame) -> pd.DataFrame:
    """Rank neighboring stations and return best alternatives."""
    if latest_station_data.empty:
        return pd.DataFrame()

    if neighbor_stations.empty:
        return pd.DataFrame()

    candidates = neighbor_stations.merge(
        latest_station_data,
        left_on="target_uid",
        right_on="uid",
        how="left"
    )

    # remove weak stations
    candidates = candidates[candidates["bikes"] >= 5]

    if candidates.empty:
        return pd.DataFrame()

   
    # Recommendation score combines multiple factors:
    # - bike availability (higher = better)
    # - historical reliability / empty rate (lower empty rate = better)
    # - walking distance (closer = better)

    # We use weights to control both:
    # 1. the importance of each factor
    # 2. the influence of different value ranges (e.g. distance is much larger than bike counts)

    # This creates a trade-off between availability, reliability, and proximity.
    candidates["recommendation_score"] = (
        candidates["bikes"] * 0.5
        + (100 - candidates["empty_rate"]) * 0.3
        - candidates["distance_meters"] * 0.02
    )

    candidates = candidates.sort_values("recommendation_score", ascending=False)

    return candidates.iloc[[0]] if not candidates.empty else pd.DataFrame()

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

    # Combined recommendation score
    candidates["recommendation_score"] = (
        + candidates["bikes"] * 0.5
        - (candidates["distance_meters"] * 0.3
        + candidates["demand_trend"] * 0.2)
    )

    candidates = candidates.sort_values("recommendation_score", ascending=False)

    #print(candidates.head(15)[["name", "bikes", "recommendation_score"]])

    return candidates.head(top_n).reset_index(drop=True)