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

    # recommendation score calculation based on bikes, empty rate, and distance
    # explaination:
    # - bikes: 0.5 because it's the most important factor for a user looking for an alternative station 
    # - empty_rate: 0.3 because a station with a high empty rate is less likely to have bikes available, but it's not as critical as the number of bikes currently available
    # - distance: 0.02 because while proximity is important, users may be willing to walk a bit further for a station with more bikes and a lower empty rate
    candidates["recommendation_score"] = (
        candidates["bikes"] * 0.5
        + (100 - candidates["empty_rate"]) * 0.3
        - candidates["distance_meters"] * 0.02
    )

    candidates = candidates.sort_values("recommendation_score", ascending=False)

    return candidates.iloc[[0]] if not candidates.empty else pd.DataFrame()