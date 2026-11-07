"""Demand trend over a fixed time window (issue #10), against the SQLite test DB."""
from datetime import datetime, timedelta

import pytest

from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.models.metrics import (
    get_bike_delta,
    get_latest_station_data,
    get_trend_reference_snapshot,
)

LATEST = datetime(2026, 11, 6, 8, 30)


@pytest.fixture
def two_stations(db_session):
    for uid in (1, 2):
        db_session.add(Station(uid=uid, name=f"S{uid}", lat=49.4875, lng=8.4660, bike_racks=10))
    db_session.flush()
    return db_session


def add_snapshots(db, bikes_by_age_min: dict[int, tuple[int, int]]) -> None:
    """bikes_by_age_min: {minutes before LATEST: (bikes station 1, bikes station 2)}"""
    for age, bikes in bikes_by_age_min.items():
        for uid, b in zip((1, 2), bikes):
            db.add(StationStatus(
                uid=uid, timestamp=LATEST - timedelta(minutes=age), bikes=b, free_racks=10 - b,
            ))
    db.commit()


# ── get_trend_reference_snapshot ─────────────────────────────────────

def test_reference_is_newest_snapshot_in_window(two_stations):
    add_snapshots(two_stations, {age: (5, 5) for age in (0, 30, 60, 90, 120)})
    assert get_trend_reference_snapshot(two_stations, LATEST) == LATEST - timedelta(minutes=60)


def test_reference_window_bounds_are_inclusive(two_stations):
    add_snapshots(two_stations, {0: (5, 5), 90: (5, 5)})
    assert get_trend_reference_snapshot(two_stations, LATEST) == LATEST - timedelta(minutes=90)


def test_reference_none_when_only_recent_snapshots(two_stations):
    add_snapshots(two_stations, {0: (5, 5), 30: (5, 5)})
    assert get_trend_reference_snapshot(two_stations, LATEST) is None


def test_reference_none_after_pipeline_gap(two_stations):
    add_snapshots(two_stations, {0: (5, 5), 180: (5, 5)})
    assert get_trend_reference_snapshot(two_stations, LATEST) is None


def test_reference_window_is_configurable(two_stations):
    add_snapshots(two_stations, {0: (5, 5), 30: (5, 5)})
    ref = get_trend_reference_snapshot(
        two_stations, LATEST, min_age=timedelta(minutes=30), max_age=timedelta(minutes=45)
    )
    assert ref == LATEST - timedelta(minutes=30)


# ── get_bike_delta ───────────────────────────────────────────────────

def test_bike_delta_defaults_to_previous_snapshot(two_stations):
    add_snapshots(two_stations, {0: (6, 4), 30: (9, 1), 60: (2, 8)})
    deltas = {r.uid: r.bike_delta for r in get_bike_delta(two_stations, LATEST)}
    assert deltas == {1: -3, 2: 3}


def test_bike_delta_with_reference_time(two_stations):
    add_snapshots(two_stations, {0: (6, 4), 30: (9, 1), 60: (2, 8)})
    deltas = {
        r.uid: r.bike_delta
        for r in get_bike_delta(two_stations, LATEST, LATEST - timedelta(minutes=60))
    }
    assert deltas == {1: 4, 2: -4}


# ── demand_score in get_latest_station_data ──────────────────────────

def test_demand_score_uses_fixed_window_not_previous_snapshot(two_stations):
    # 60 min ago: 2 / 8 bikes; 30 min ago: 9 / 1 bikes; now: 6 / 4 bikes
    add_snapshots(two_stations, {0: (6, 4), 30: (9, 1), 60: (2, 8)})
    df = get_latest_station_data(two_stations).set_index("uid")
    assert df.loc[1, "demand_score"] == 4    # 6 - 2, not 6 - 9
    assert df.loc[2, "demand_score"] == -4   # 4 - 8, not 4 - 1


def test_demand_score_nan_after_gap(two_stations):
    add_snapshots(two_stations, {0: (6, 4), 180: (0, 10)})
    assert get_latest_station_data(two_stations)["demand_score"].isna().all()


def test_demand_score_nan_without_history(two_stations):
    add_snapshots(two_stations, {0: (6, 4)})
    assert get_latest_station_data(two_stations)["demand_score"].isna().all()


def test_demand_score_nan_for_seeded_30min_data(seeded_db):
    # Seed data has only two snapshots 30 min apart -> outside the trend window
    assert get_latest_station_data(seeded_db)["demand_score"].isna().all()


def test_station_new_since_reference_gets_zero_delta(two_stations):
    add_snapshots(two_stations, {0: (6, 4), 60: (2, 8)})
    two_stations.add(Station(uid=3, name="New", lat=49.4875, lng=8.4660, bike_racks=10))
    two_stations.add(StationStatus(uid=3, timestamp=LATEST, bikes=5, free_racks=5))
    two_stations.commit()
    df = get_latest_station_data(two_stations).set_index("uid")
    assert df.loc[3, "demand_score"] == 0
