import pandas as pd

from script.models.metrics import calculate_empty_rate
from script.models.recommendations import score_stations_for_user

class RecommendationService:
    """Service class for station recommendations based on user location."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.latest_snapshot: pd.Timestamp = df["snapshot_time"].max()

        # Latest snapshot data
        self.latest_data = df[df["snapshot_time"] == self.latest_snapshot].copy()

        # Historical empty rates
        self.empty_rates = calculate_empty_rate(df)

    def get_recommendations_for_location(self, lat: float, lng: float, top_n: int = 5) -> dict:
        """GPS-based: Return top-N station recommendations for a user location."""
        scored = score_stations_for_user(
            self.latest_data,
            self.empty_rates,
            user_lat=lat,
            user_lng=lng,
            top_n=top_n,
        )

        recommendations = []
        for rank, (_, row) in enumerate(scored.iterrows(), start=1):
            recommendations.append({
                "rank": rank,
                "uid": int(row["uid"]),
                "name": row["name"] if pd.notna(row.get("name")) else "Unknown",
                "lat": float(row["lat"]),
                "lng": float(row["lng"]),
                "bikes": int(row["bikes"]),
                "free_racks": int(row["free_racks"]) if pd.notna(row.get("free_racks")) else 0,
                "occupancy_pct": round(float(row["occupancy_pct"]), 1) if pd.notna(row.get("occupancy_pct")) else 0.0,
                "status": row["status"] if pd.notna(row.get("status")) else "Unknown",
                "distance_meters": round(float(row["distance_meters"]), 1),
                "empty_rate": round(float(row["empty_rate"]), 1),
                "recommendation_score": round(float(row["recommendation_score"]), 1),
            })

        return {
            "user_location": {"lat": lat, "lng": lng},
            "recommendations": recommendations,
        }
