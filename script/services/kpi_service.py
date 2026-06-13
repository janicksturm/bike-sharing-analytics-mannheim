import pandas as pd

class KpiService:
    """Service class for computing KPI status metrics from preprocessed snapshot data."""

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.snapshots: list[pd.Timestamp] = sorted(df["snapshot_time"].unique())

    def get_status(self) -> dict:
        """Compute KPI metrics for the latest snapshot and compare them against the immediately preceding snapshot."""
        selected_ts = self.snapshots[-1]
        df_cur = self.df[self.df["snapshot_time"] == selected_ts]

        #new
        cur_total_bikes = int(df_cur["bikes"].sum())
        cur_available = int((df_cur["bikes"] > 0).sum())
        cur_empty = int((df_cur["bikes"] == 0).sum())
        cur_avg_occ = round(float(df_cur["occupancy_pct"].mean()), 1)

        #previous
        prev_snapshots = [s for s in self.snapshots if s < selected_ts]

        if prev_snapshots:
            df_prev = self.df[self.df["snapshot_time"] == prev_snapshots[-1]]
            prev_total_bikes = int(df_prev["bikes"].sum())
            prev_available = int((df_prev["bikes"] > 0).sum())
            prev_empty = int((df_prev["bikes"] == 0).sum())
            prev_avg_occ = round(float(df_prev["occupancy_pct"].mean()), 1)
        else:
            prev_total_bikes = prev_available = prev_empty = prev_avg_occ = None

        return {
            "snapshot_time": selected_ts.isoformat(),
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