import pandas as pd

from .preprocessing_service import PreProcessingService

class KpiService:
    """Service class for computing KPI status metrics from preprocessed snapshot data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.snapshots: list[pd.Timestamp] = sorted(df["snapshot_time"].unique())

    def get_status(self) -> dict:
        """Compute KPI metrics for the latest snapshot and compare them against the immediately preceding snapshot."""
        latest_ts = self.snapshots[-1]
        latest_df = self.df[self.df["snapshot_time"] == latest_ts]

        cur_total_bikes = int(latest_df["bikes"].sum())
        cur_available = int((latest_df["bikes"] > 0).sum())
        cur_empty = int((latest_df["bikes"] == 0).sum())
        cur_avg_occ = round(float(latest_df["occupancy_pct"].mean()), 1)

        if len(self.snapshots) <= 1:
            return {
                "snapshot_time": latest_ts.isoformat(),
                "total_bikes": {"value": cur_total_bikes, "delta": None},
                "available_to_rent": {"value": cur_available, "delta": None},
                "empty_stations": {"value": cur_empty, "delta": None},
                "avg_occupancy": {"value": cur_avg_occ, "delta": None},
            }
        previous_df = self.df[self.df["snapshot_time"] == self.snapshots[-2]]

        prev_total_bikes = previous_df["bikes"].sum()
        prev_available = (previous_df["bikes"] > 0).sum()
        prev_empty = (previous_df["bikes"] == 0).sum()
        prev_avg_occ = round(previous_df["occupancy_pct"].mean(), 1)

        return {
            "snapshot_time": latest_ts.isoformat(),
            "total_bikes": {
                "value": cur_total_bikes,
                "delta": self._delta(cur_total_bikes, prev_total_bikes),
            },
            "available_to_rent": {
                "value": cur_available,
                "delta": self._delta(cur_available, prev_available),
            },
            "empty_stations": {
                "value": cur_empty,
                "delta": self._delta(cur_empty, prev_empty),
            },
            "avg_occupancy": {
                "value": cur_avg_occ,
                "delta": self._delta(cur_avg_occ, prev_avg_occ),
            },
        }

    def _delta(self, cur: float, prev: float):
        """Compute the delta between the current and previous value."""
        return round(cur - prev, 1) if prev is not None else None