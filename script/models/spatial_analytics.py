import pandas as pd
from models.utils import haversine

RADIUS_METERS = 500

"""
This module provides functions to analyze the spatial relationships between stations, such as calculating distances and finding neighboring stations within a specified radius.
"""
def build_station_distance_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Builds a distance matrix for stations based on their latitude and longitude."""

    stations = (
        df[["uid", "name", "lat", "lng"]]
        .drop_duplicates()
    )

    rows = []

    for _, station_a in stations.iterrows():
        for _, station_b in stations.iterrows():

            if station_a["uid"] == station_b["uid"]:
                continue

            distance = haversine(
                station_a["lat"],
                station_a["lng"],
                station_b["lat"],
                station_b["lng"]
            )

            rows.append({
                "source_uid": station_a["uid"],
                "target_uid": station_b["uid"],
                "distance_meters": distance
            })

    return pd.DataFrame(rows)


def get_neighbor_stations(station_uid, distance_df, radius=RADIUS_METERS):
    """Returns a DataFrame of neighboring stations within a specified radius for a given station UID."""

    neighbors = distance_df[(distance_df["source_uid"] == station_uid) & (distance_df["distance_meters"] <= radius)]

    return neighbors.sort_values("distance_meters")
