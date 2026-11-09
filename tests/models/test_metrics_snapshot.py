"""Snapshot-level metric functions, against the seeded SQLite test DB.

Seed (see conftest): 4 stations, snapshots T0 and T1.
    T0 bikes: 4, 0, 6, 2  (free racks 6, 8, 6, 0)
    T1 bikes: 6, 1, 0, 0  (free racks 4, 7, 12, 0)
"""
import pandas as pd
import pytest

from src.nextbike_prediction.models.metrics import (
    calculate_empty_rate,
    compute_station_metrics,
    get_latest_snapshot,
    get_latest_station_data,
    get_previous_snapshot,
    get_station_status,
    get_total_bikes,
)
from tests.conftest import SEED_METRICS, T0, T1

# snapshot lookup

def test_latest_snapshot(seeded_db):
    assert get_latest_snapshot(seeded_db) == T1


def test_latest_snapshot_none_without_data(db_session):
    assert get_latest_snapshot(db_session) is None


def test_previous_snapshot(seeded_db):
    assert get_previous_snapshot(seeded_db, T1) == T0


def test_previous_snapshot_none_for_first(seeded_db):
    assert get_previous_snapshot(seeded_db, T0) is None


# per-snapshot aggregates

@pytest.mark.parametrize("ts, expected", [(T0, 12), (T1, 7)])
def test_total_bikes(seeded_db, ts, expected):
    assert get_total_bikes(seeded_db, ts) == expected


def test_total_bikes_none_without_data(db_session):
    assert get_total_bikes(db_session, T1) is None


@pytest.mark.parametrize("ts, expected", [(T0, 1), (T1, 2)])
def test_empty_station_count(seeded_db, ts, expected):
    assert calculate_empty_rate(seeded_db, ts) == expected


def test_station_status_labels(seeded_db):
    rows = {row.uid: (row.bikes, row.status) for row in get_station_status(seeded_db, T1)}
    assert rows == {
        1: (6, "Available"),
        2: (1, "Low"),
        3: (0, "Empty"),
        4: (0, "Empty"),
    }


# compute_station_metrics

def test_compute_station_metrics_matches_seed(seeded_db):
    # SEED_METRICS holds the hand-computed values for the seeded snapshots;
    # station 4's T1 occupancy is NULL (0 bikes, 0 racks) and is skipped by AVG.
    metrics = {m["uid"]: m for m in compute_station_metrics(seeded_db)}
    assert set(metrics) == {1, 2, 3, 4}
    for uid, _, empty_rate, avg_bikes, avg_occupancy in SEED_METRICS:
        assert metrics[uid]["empty_rate"] == pytest.approx(empty_rate)
        assert metrics[uid]["avg_bikes"] == pytest.approx(avg_bikes)
        assert metrics[uid]["avg_occupancy"] == pytest.approx(avg_occupancy)


def test_compute_station_metrics_empty_db(db_session):
    assert compute_station_metrics(db_session) == []


# get_latest_station_data

def test_latest_station_data_columns_and_values(seeded_db):
    df = get_latest_station_data(seeded_db).set_index("uid")
    assert list(df.columns) == [
        "name", "lat", "lng", "bikes", "free_racks", "occupancy_pct", "demand_score",
    ]
    assert df["bikes"].to_dict() == {1: 6, 2: 1, 3: 0, 4: 0}
    assert df.loc[1, "occupancy_pct"] == pytest.approx(60.0)
    assert df.loc[2, "occupancy_pct"] == pytest.approx(12.5)
    assert df.loc[3, "occupancy_pct"] == pytest.approx(0.0)
    assert pd.isna(df.loc[4, "occupancy_pct"])  # no bikes and no free racks


def test_latest_station_data_empty_db(db_session):
    df = get_latest_station_data(db_session)
    assert df.empty
    assert "occupancy_pct" in df.columns
