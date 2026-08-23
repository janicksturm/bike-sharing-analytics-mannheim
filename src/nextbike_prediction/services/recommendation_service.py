import pandas as pd
from sqlalchemy.orm import Session

from src.nextbike_prediction.models.metrics import get_latest_station_data, get_station_empty_rates
from src.nextbike_prediction.models.recommendations import score_stations_for_user

class RecommendationService:
    """Service class for station recommendations based on user location."""

    def __init__(self, db: Session):
        self.db = db

    def get_recommendations_for_location(self, lat: float, lng: float, top_n: int = 5, exclude_uid: int | None = None) -> dict:
        """GPS-based: Return top-N station recommendations for a user location."""
        latest_data = get_latest_station_data(self.db)
        empty_rates = get_station_empty_rates(self.db)

        scored = score_stations_for_user(
            latest_data,
            empty_rates,
            user_lat=lat,
            user_lng=lng,
            top_n=top_n,
            exclude_uid=exclude_uid,
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
                "distance_meters": round(float(row["distance_meters"]), 1),
                "empty_rate": round(float(row["empty_rate"]), 1),
                "demand_score": round(float(row["demand_score"]), 2) if pd.notna(row.get("demand_score")) else None,
                "recommendation_score": round(float(row["recommendation_score"]), 4),
            })

        return {"recommendations": recommendations}
