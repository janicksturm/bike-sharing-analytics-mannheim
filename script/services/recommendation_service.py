import pandas as pd
from script.models.preprocessing import load_all_snapshots
from script.models.spatial_analytics import build_station_distance_matrix, get_neighbor_stations
from script.models.metrics import calculate_empty_rate
from script.models.recommendations import best_possible_station

class RecommendationService:
    def __init__(self):
        self.df = load_all_snapshots()
        self.distance_df = build_station_distance_matrix(self.df)
        self.latest_data = self.df.groupby("uid").tail(1).reset_index(drop=True)

        empty_rates = calculate_empty_rate(self.df)
        self.latest_data = self.latest_data.merge(empty_rates, on="uid", how="left")

    def get_recommendations(self, station_uid: int, neighbors: pd.DataFrame) -> pd.DataFrame:
        """Get the best alternative station for a given station."""
        return best_possible_station(self.latest_data, neighbors)