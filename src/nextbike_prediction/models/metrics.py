import datetime

import pandas as pd
from requests import Session
from sqlalchemy import case, func, select

from nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus

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
        StationStatus.station_uid,
        StationStatus.bikes,
        status,
    ).where(
        StationStatus.timestamp == snapshot_time
    )
    return db.execute(statement).all()