import numpy as np
import pandas as pd
from .utils import haversine


WEIGHT_BIKES = 0.25
WEIGHT_RELIABILITY = 0.10
WEIGHT_DISTANCE = 0.40
WEIGHT_TREND = 0.25

BIKE_SATURATION = 8
DISTANCE_DECAY_METERS = 800
EMPTY_RATE_DECAY = 4
TREND_SCALE_BIKES = 3

MAX_DISTANCE_METERS = 800
MIN_BIKES = 1


def trend_score(demand: pd.Series) -> pd.Series:
    """Map a bike delta to [0, 1] on a fixed scale; 0 or unknown -> 0.5 (neutral).

    Independent of the other candidates, unlike min-max normalization.
    """
    return 0.5 + 0.5 * np.tanh(demand.fillna(0) / TREND_SCALE_BIKES)


def score_stations_for_user(latest_data: pd.DataFrame, empty_rates: pd.DataFrame, user_lat: float, user_lng: float, top_n: int = 5, exclude_uid: int | None = None) -> pd.DataFrame:
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
    # Stations without history get the median empty rate (neutral)
    median_empty_rate = candidates["empty_rate"].median()
    candidates["empty_rate"] = candidates["empty_rate"].fillna(
        median_empty_rate if pd.notna(median_empty_rate) else 0
    )

    if exclude_uid is not None:
        candidates = candidates[candidates["uid"] != exclude_uid].copy()

    # Compute distance from user to each station
    candidates["distance_meters"] = candidates.apply(
        lambda row: haversine(user_lat, user_lng, row["lat"], row["lng"]),
        axis=1,
    )

    # Only consider nearby stations that currently have bikes
    candidates = candidates[
        (candidates["bikes"] >= MIN_BIKES)
        & (candidates["distance_meters"] <= MAX_DISTANCE_METERS)
    ].copy()

    if candidates.empty:
        return pd.DataFrame()

    # demand_score is the bike delta over the last 60–90 min (NaN if unknown):
    # positive = bikes returning = good
    candidates["demand_trend"] = candidates["demand_score"].fillna(0)

    bike_score = 1 - np.exp(-candidates["bikes"] / BIKE_SATURATION)
    distance_score = np.exp(-candidates["distance_meters"] / DISTANCE_DECAY_METERS)
    reliability_score = np.exp(-EMPTY_RATE_DECAY * candidates["empty_rate"])

    candidates["recommendation_score"] = (
        WEIGHT_BIKES * bike_score
        + WEIGHT_RELIABILITY * reliability_score
        + WEIGHT_DISTANCE * distance_score
        + WEIGHT_TREND * trend_score(candidates["demand_trend"])
    )

    candidates = candidates.sort_values("recommendation_score", ascending=False)
    return candidates.head(top_n).reset_index(drop=True)