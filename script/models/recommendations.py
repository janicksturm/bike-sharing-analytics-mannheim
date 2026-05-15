import pandas as pd


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