import pandas as pd

from script.services.preprocessing_service import PreProcessingService


class LocationService:
    """Service class for retrieving station location and live status data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.latest_snapshot: pd.Timestamp = df["snapshot_time"].max()

    def get_stations(self) -> list[dict]:
        """Return all stations for the latest snapshot with live status fields."""
        df_cur = self.df[self.df["snapshot_time"] == self.latest_snapshot].copy()

        df_cur = df_cur[[
            "uid",
            "name",
            "lat",
            "lng",
            "bikes",
            "free_racks",
            "occupancy_pct",
            "bikes_available_to_rent",
            "status",
        ]].drop_duplicates(subset=["uid"])

        # Ensure numeric types are JSON-serialisable
        df_cur["uid"] = df_cur["uid"].astype(int)
        df_cur["bikes"] = df_cur["bikes"].astype(int)
        df_cur["free_racks"] = df_cur["free_racks"].astype(int)
        df_cur["occupancy_pct"] = df_cur["occupancy_pct"].fillna(0.0).round(1)
        df_cur["bikes_available_to_rent"] = (
            df_cur["bikes_available_to_rent"].fillna(0).astype(int)
        )

        return df_cur.to_dict(orient="records")