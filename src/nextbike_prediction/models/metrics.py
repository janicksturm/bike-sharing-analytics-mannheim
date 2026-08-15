import datetime

import pandas as pd
from requests import Session
from sqlalchemy import func, select

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

# We want to calculate how full each bike station is. 
# First, we find out the total number of spaces by adding the number of bikes currently there and the number of free racks. 
# Then, we calculate the percentage of those spaces that are occupied by bikes. 
# If there are no spaces available (total capacity is zero), we avoid dividing by zero 
# by only calculating the percentage where the total capacity is greater than zero. 
def calculate_station_occupancy_capacity(df: pd.DataFrame) -> pd.Series:
    _capacity = df["total_capacity"].astype(float)
    return (
        (df["bikes"] / _capacity.where(_capacity > 0) * 100)
        .fillna(0)
        .round(1)
    )