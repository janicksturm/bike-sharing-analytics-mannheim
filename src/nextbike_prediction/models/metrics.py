from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import Integer, case, cast, extract, func, select
from sqlalchemy.orm import Session

from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.database.models.station_metrics import StationMetrics

# Demand trend: compare the latest snapshot with one taken 60–90 min earlier.
# If no snapshot falls into that window (pipeline gap), no trend is reported,
# so gaps don't turn into multi-hour deltas.
TREND_WINDOW_MIN = timedelta(minutes=60)
TREND_WINDOW_MAX = timedelta(minutes=90)

# Time-of-day empty rate: minimum observations a station needs in the
# (hour x weekday/weekend) slot before the slot value replaces its overall rate.
MIN_SLOT_OBSERVATIONS = 4


def compute_station_metrics(db: Session):
    """Compute metrics for each station based on historical data.

    Returns a list of dictionaries with keys:
        uid, empty_rate, avg_bikes, avg_occupancy
    """
    latest_ts = get_latest_snapshot(db)
    if latest_ts is None:
        return []

    statement = (
        select(
            StationStatus.uid,
            func.avg(StationStatus.bikes).label("avg_bikes"),
            func.avg(
                case(
                    (StationStatus.bikes + StationStatus.free_racks > 0,
                     StationStatus.bikes * 100.0 / (StationStatus.bikes + StationStatus.free_racks)),
                    else_=None,
                )
            ).label("avg_occupancy"),
            func.avg(case((StationStatus.bikes == 0, 1.0), else_=0.0)).label("empty_rate"),
        )
        .where(StationStatus.timestamp <= latest_ts)
        .group_by(StationStatus.uid)
    )

    results = db.execute(statement).all()
    metrics = [
        {
            "uid": row.uid,
            "empty_rate": row.empty_rate,
            "avg_bikes": row.avg_bikes,
            "avg_occupancy": row.avg_occupancy,
        }
        for row in results
    ]
    return metrics


"""
This module contains functions for calculating various metrics from the bike-sharing data.
"""
def calculate_empty_rate(db: Session, snapshot_time: datetime):
    """Calculate the percentage of time each station is empty."""
    return db.scalar(
        select(func.count())
        .filter(StationStatus.bikes == 0)
        .where(
            StationStatus.timestamp == snapshot_time
        )
    )

def get_latest_snapshot(db: Session):
    """Return the timestamp of the latest snapshot in the database."""
    return db.scalar(
        select(
            func.max(StationStatus.timestamp)
        )
    )

def get_previous_snapshot(db: Session, latest_ts: datetime):
    """Return the timestamp of the snapshot immediately preceding latest_ts."""
    return db.scalar(
        select(func.max(StationStatus.timestamp))
        .where(StationStatus.timestamp < latest_ts)
    )

def get_total_bikes(db: Session, snapshot_time: datetime):
    """Return the total number of bikes available across all stations at the latest snapshot."""
    return db.scalar(
        select(
            func.sum(StationStatus.bikes)
        )
        .where(
            StationStatus.timestamp == snapshot_time
        )
    )

def get_avg_occupancy(db: Session, snapshot_time: datetime):
    """Return the average occupancy rate across all stations at the latest snapshot."""
    return db.scalar(
        select(
            func.avg(
                StationStatus.bikes * 100.0
                / (StationStatus.bikes + Station.bike_racks)
            )
        )
        .join(Station, Station.uid == StationStatus.uid)
        .where(
            StationStatus.timestamp == snapshot_time,
            StationStatus.bikes + Station.bike_racks > 0
        )
    )

def get_total_capacity(db: Session, snapshot_time: datetime):
    """Return the total capacity (bikes + free racks) across all stations at the latest snapshot."""
    return db.scalar(
        select(
            func.sum(StationStatus.bikes + Station.bike_racks)
        )
        .join(Station, Station.uid == StationStatus.uid)
        .where(
            StationStatus.timestamp == snapshot_time
        )
    )

def get_station_status(db: Session, snapshot_time: datetime):
    """Return a list of stations with their current status (Empty, Low, Available)."""
    status = case(
        (StationStatus.bikes == 0, "Empty"),
        (StationStatus.bikes <= 2, "Low"),
        else_="Available",
    ).label("status")

    statement = select(
        StationStatus.uid,
        StationStatus.bikes,
        status,
    ).where(
        StationStatus.timestamp == snapshot_time
    )
    return db.execute(statement).all()

def get_trend_reference_snapshot(
    db: Session,
    latest_ts: datetime,
    min_age: timedelta = TREND_WINDOW_MIN,
    max_age: timedelta = TREND_WINDOW_MAX,
):
    """Return the most recent snapshot that is between min_age and max_age
    older than latest_ts, or None if there is no snapshot in that window."""
    return db.scalar(
        select(func.max(StationStatus.timestamp))
        .where(
            StationStatus.timestamp <= latest_ts - min_age,
            StationStatus.timestamp >= latest_ts - max_age,
        )
    )

def get_bike_delta(db: Session, snapshot_time: datetime, reference_time: datetime | None = None):
    """Return the change in bike count for each station between reference_time
    and snapshot_time. Defaults to the immediately preceding snapshot."""
    prev_ts = reference_time if reference_time is not None else get_previous_snapshot(db, snapshot_time)
    if prev_ts is None:
        return []

    curr = (
        select(StationStatus.uid, StationStatus.bikes.label("curr_bikes"))
        .where(StationStatus.timestamp == snapshot_time)
        .subquery()
    )
    prev = (
        select(StationStatus.uid, StationStatus.bikes.label("prev_bikes"))
        .where(StationStatus.timestamp == prev_ts)
        .subquery()
    )
    statement = (
        select(
            curr.c.uid,
            (curr.c.curr_bikes - func.coalesce(prev.c.prev_bikes, curr.c.curr_bikes)).label("bike_delta"),
        )
        .outerjoin(prev, curr.c.uid == prev.c.uid)
    )

    return db.execute(statement).all()

def get_latest_station_data(db: Session) -> pd.DataFrame:
    """Return the latest snapshot data for all stations, including a demand_score.

    demand_score is the bike delta over the fixed trend window
    (TREND_WINDOW_MIN–TREND_WINDOW_MAX before the latest snapshot); it is NaN
    when no snapshot exists in that window.

    Returns a DataFrame with columns:
        uid, name, lat, lng, bikes, free_racks, occupancy_pct, demand_score
    """
    latest_ts = get_latest_snapshot(db)
    if latest_ts is None:
        return pd.DataFrame(columns=[
            "uid", "name", "lat", "lng", "bikes", "free_racks",
            "occupancy_pct", "demand_score",
        ])

    reference_ts = get_trend_reference_snapshot(db, latest_ts)
    delta_rows = get_bike_delta(db, latest_ts, reference_ts) if reference_ts is not None else []
    demand_map = {row.uid: row.bike_delta for row in delta_rows}

    statement = (
        select(
            Station.uid,
            Station.name,
            Station.lat,
            Station.lng,
            StationStatus.bikes,
            StationStatus.free_racks,
            case(
                (StationStatus.bikes + StationStatus.free_racks > 0,
                 StationStatus.bikes * 100.0 / (StationStatus.bikes + StationStatus.free_racks)),
                else_=None,
            ).label("occupancy_pct"),
        )
        .join(Station, Station.uid == StationStatus.uid)
        .where(StationStatus.timestamp == latest_ts)
        .order_by(Station.uid)
    )

    rows = db.execute(statement).all()
    df = pd.DataFrame(rows, columns=[
        "uid", "name", "lat", "lng", "bikes", "free_racks", "occupancy_pct",
    ])

    if df.empty:
        return df

    df["demand_score"] = df["uid"].map(demand_map)
    return df.reset_index(drop=True)

def get_slot_empty_rates(db: Session, reference_time: datetime) -> pd.DataFrame:
    """Return per-station empty rates for the time slot of reference_time.

    A slot is the hour of day combined with weekday vs. weekend, so a station
    that is regularly empty at 8:00 on weekdays gets a high rate at that time
    only. Hours are evaluated in the timezone the timestamps are stored in.
    Only snapshots up to reference_time are considered.

    Returns a DataFrame with columns:
        uid, empty_rate, observations
    """
    hour = cast(extract("hour", StationStatus.timestamp), Integer)
    day_of_week = cast(extract("dow", StationStatus.timestamp), Integer)  # 0 = Sunday
    is_weekend = day_of_week.in_([0, 6])
    slot_is_weekend = reference_time.weekday() >= 5  # Python: 5 = Sat, 6 = Sun

    statement = (
        select(
            StationStatus.uid,
            func.avg(case((StationStatus.bikes == 0, 1.0), else_=0.0)).label("empty_rate"),
            func.count().label("observations"),
        )
        .where(
            hour == reference_time.hour,
            is_weekend if slot_is_weekend else ~is_weekend,
            StationStatus.timestamp <= reference_time,
        )
        .group_by(StationStatus.uid)
        .order_by(StationStatus.uid)
    )
    rows = db.execute(statement).all()
    return pd.DataFrame(rows, columns=["uid", "empty_rate", "observations"])

def get_station_empty_rates(
    db: Session,
    reference_time: datetime | None = None,
    min_slot_observations: int = MIN_SLOT_OBSERVATIONS,
) -> pd.DataFrame:
    """Return the empty rate (0..1) for every station.

    With reference_time, the time-slot rate is used for stations with at least
    min_slot_observations in that slot; all others fall back to their overall
    rate. Without reference_time, only the overall rate is returned.

    Returns a DataFrame with columns:
        uid, empty_rate
    """
    overall = get_overall_empty_rates(db)
    if reference_time is None:
        return overall

    slot = get_slot_empty_rates(db, reference_time)
    slot = slot[slot["observations"] >= min_slot_observations]
    if slot.empty:
        return overall

    combined = (
        slot.set_index("uid")["empty_rate"].astype(float)
        .combine_first(overall.set_index("uid")["empty_rate"].astype(float))
        .sort_index()
    )
    return combined.rename_axis("uid").reset_index(name="empty_rate")

def get_overall_empty_rates(db: Session) -> pd.DataFrame:
    """Return the latest persisted (all-time) empty rates for all stations.

    Returns a DataFrame with columns:
        uid, empty_rate
    """
    latest_ts = db.scalar(
        select(func.max(StationMetrics.timestamp))
    )
    if latest_ts is None:
        return pd.DataFrame(columns=["uid", "empty_rate"])

    statement = (
        select(
            StationMetrics.uid,
            StationMetrics.empty_rate,
        )
        .where(StationMetrics.timestamp == latest_ts)
        .order_by(StationMetrics.uid)
    )

    rows = db.execute(statement).all()
    df = pd.DataFrame(rows, columns=["uid", "empty_rate"])
    return df.reset_index(drop=True)