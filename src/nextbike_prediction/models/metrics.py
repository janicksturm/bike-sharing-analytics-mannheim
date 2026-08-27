import datetime

import pandas as pd
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.database.models.station_metrics import StationMetrics


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
            (func.sum(case((StationStatus.bikes == 0, 1), else_=0)) / func.count()).label("empty_rate"),
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

def get_bike_delta(db: Session, snapshot_time: datetime):
    """Return the change in bike count for each station compared to the previous snapshot."""
    previous_bike = func.lag(StationStatus.bikes).over(
        partition_by=StationStatus.uid,
        order_by=StationStatus.timestamp
    )

    statement = select(
        StationStatus.uid,
        (StationStatus.bikes - previous_bike).label("bike_delta")
    ).where(
        StationStatus.timestamp == snapshot_time
    )

    return db.execute(statement).all()

def get_latest_station_data(db: Session) -> pd.DataFrame:
    """Return the latest snapshot data for all stations, including a demand_score.

    Returns a DataFrame with columns:
        uid, name, lat, lng, bikes, free_racks, occupancy_pct, demand_score
    """
    latest_ts = get_latest_snapshot(db)
    if latest_ts is None:
        return pd.DataFrame(columns=[
            "uid", "name", "lat", "lng", "bikes", "free_racks",
            "occupancy_pct", "demand_score",
        ])


    delta_rows = get_bike_delta(db, latest_ts)
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

def get_station_empty_rates(db: Session) -> pd.DataFrame:
    """Return the empty rates for all stations based on historical data.

    Returns a DataFrame with columns:
        uid, empty_rate
    """
    statement = (
        select(
            StationMetrics.uid,
            StationMetrics.empty_rate,
        )
        .order_by(StationMetrics.uid)
    )

    rows = db.execute(statement).all()
    df = pd.DataFrame(rows, columns=["uid", "empty_rate"])
    return df.reset_index(drop=True)