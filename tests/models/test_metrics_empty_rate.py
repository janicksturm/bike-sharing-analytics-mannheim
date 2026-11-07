"""Time-of-day empty rate with fallback (issue #10), against the SQLite test DB."""
from datetime import datetime

import pytest

from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_metrics import StationMetrics
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.models.metrics import (
    MIN_SLOT_OBSERVATIONS,
    get_overall_empty_rates,
    get_slot_empty_rates,
    get_station_empty_rates,
)

LATEST = datetime(2026, 11, 8, 12, 0)  # Sunday noon, after all test data
WEEKDAYS = [datetime(2026, 11, d) for d in (2, 3, 4, 5, 6)]  # Mon–Fri
WEEKEND = [datetime(2026, 11, d) for d in (7, 8)]            # Sat, Sun


def add_station(db, uid: int) -> None:
    db.add(Station(uid=uid, name=f"S{uid}", lat=49.4875, lng=8.4660, bike_racks=10))
    db.flush()


def add_status(db, uid: int, ts: datetime, bikes: int) -> None:
    db.add(StationStatus(uid=uid, timestamp=ts, bikes=bikes, free_racks=10 - bikes))


def add_overall_rate(db, uid: int, empty_rate: float, ts: datetime = LATEST) -> None:
    db.add(StationMetrics(uid=uid, timestamp=ts, empty_rate=empty_rate, avg_bikes=None, avg_occupancy=None))


@pytest.fixture
def commuter_station(db_session):
    """Station 1: always empty weekdays 08:xx, full weekdays 20:xx and weekend 08:xx.
    Overall (all-time) empty rate: 0.6."""
    add_station(db_session, 1)
    for day in WEEKDAYS:
        add_status(db_session, 1, day.replace(hour=8), 0)
        add_status(db_session, 1, day.replace(hour=8, minute=30), 0)
        add_status(db_session, 1, day.replace(hour=20), 8)
    for day in WEEKEND:
        add_status(db_session, 1, day.replace(hour=8), 8)
    add_overall_rate(db_session, 1, 0.6)
    db_session.commit()
    return db_session


# ── get_slot_empty_rates ─────────────────────────────────────────────

def test_slot_weekday_morning(commuter_station):
    row = get_slot_empty_rates(commuter_station, datetime(2026, 11, 6, 8, 30)).set_index("uid").loc[1]
    assert row["empty_rate"] == pytest.approx(1.0)
    assert row["observations"] == 10


def test_slot_weekday_evening(commuter_station):
    df = get_slot_empty_rates(commuter_station, datetime(2026, 11, 6, 20, 0))
    assert df.set_index("uid").loc[1, "empty_rate"] == pytest.approx(0.0)


def test_slot_matches_hour_not_minute(commuter_station):
    # 08:59 is still the 8 o'clock slot
    df = get_slot_empty_rates(commuter_station, datetime(2026, 11, 6, 8, 59))
    assert df.set_index("uid").loc[1, "observations"] == 10


def test_slot_separates_weekend_from_weekday(commuter_station):
    row = get_slot_empty_rates(commuter_station, datetime(2026, 11, 8, 8, 0)).set_index("uid").loc[1]
    assert row["empty_rate"] == pytest.approx(0.0)
    assert row["observations"] == 2


def test_slot_saturday_counts_as_weekend(commuter_station):
    df = get_slot_empty_rates(commuter_station, datetime(2026, 11, 7, 8, 0))
    assert df.set_index("uid").loc[1, "observations"] == 1  # only Saturday 08:00 so far


def test_slot_ignores_rows_after_reference_time(commuter_station):
    df = get_slot_empty_rates(commuter_station, datetime(2026, 11, 3, 8, 15))  # Tue
    # Only Mon 08:00, Mon 08:30 and Tue 08:00 are <= reference time
    assert df.set_index("uid").loc[1, "observations"] == 3


def test_slot_without_data_is_empty(commuter_station):
    assert get_slot_empty_rates(commuter_station, datetime(2026, 11, 6, 3, 0)).empty


# ── get_station_empty_rates ──────────────────────────────────────────

def test_empty_rate_depends_on_time_of_request(commuter_station):
    morning = get_station_empty_rates(commuter_station, datetime(2026, 11, 6, 8, 30))
    evening = get_station_empty_rates(commuter_station, datetime(2026, 11, 6, 20, 30))
    assert morning.set_index("uid").loc[1, "empty_rate"] == pytest.approx(1.0)
    assert evening.set_index("uid").loc[1, "empty_rate"] == pytest.approx(0.0)


def test_sparse_slot_falls_back_to_overall_rate(commuter_station):
    # Weekend 08:xx has only 2 observations (< MIN_SLOT_OBSERVATIONS)
    assert MIN_SLOT_OBSERVATIONS > 2
    df = get_station_empty_rates(commuter_station, datetime(2026, 11, 8, 8, 0))
    assert df.set_index("uid").loc[1, "empty_rate"] == pytest.approx(0.6)


def test_slot_without_data_falls_back_to_overall_rate(commuter_station):
    df = get_station_empty_rates(commuter_station, datetime(2026, 11, 6, 3, 0))
    assert df.set_index("uid").loc[1, "empty_rate"] == pytest.approx(0.6)


def test_min_slot_observations_is_configurable(commuter_station):
    df = get_station_empty_rates(commuter_station, datetime(2026, 11, 8, 8, 0), min_slot_observations=2)
    assert df.set_index("uid").loc[1, "empty_rate"] == pytest.approx(0.0)


def test_fallback_is_decided_per_station(commuter_station):
    add_station(commuter_station, 2)
    add_status(commuter_station, 2, datetime(2026, 11, 6, 8, 0), 0)  # 1 observation only
    add_overall_rate(commuter_station, 2, 0.2)
    commuter_station.commit()

    df = get_station_empty_rates(commuter_station, datetime(2026, 11, 6, 8, 30)).set_index("uid")
    assert df.loc[1, "empty_rate"] == pytest.approx(1.0)  # slot value
    assert df.loc[2, "empty_rate"] == pytest.approx(0.2)  # overall fallback


def test_station_without_overall_rate_uses_slot_rate(commuter_station):
    add_station(commuter_station, 2)
    for day in WEEKDAYS:
        add_status(commuter_station, 2, day.replace(hour=8), 5)
    commuter_station.commit()

    df = get_station_empty_rates(commuter_station, datetime(2026, 11, 6, 8, 30)).set_index("uid")
    assert df.loc[2, "empty_rate"] == pytest.approx(0.0)


def test_without_reference_time_returns_overall_rate(commuter_station):
    df = get_station_empty_rates(commuter_station)
    assert df.set_index("uid").loc[1, "empty_rate"] == pytest.approx(0.6)


def test_overall_uses_latest_metrics_timestamp(commuter_station):
    add_overall_rate(commuter_station, 1, 0.9, ts=datetime(2026, 11, 1))  # older value
    commuter_station.commit()
    assert get_overall_empty_rates(commuter_station).set_index("uid").loc[1, "empty_rate"] == pytest.approx(0.6)


def test_empty_database_returns_empty_frame(db_session):
    df = get_station_empty_rates(db_session, LATEST)
    assert df.empty
    assert list(df.columns) == ["uid", "empty_rate"]
