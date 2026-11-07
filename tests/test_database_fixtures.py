"""Smoke tests that verify the SQLite test database fixtures work."""
import pytest
from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError

from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_metrics import StationMetrics
from src.nextbike_prediction.database.models.station_status import StationStatus
from tests.conftest import SEED_METRICS, SEED_STATIONS, SEED_STATUS, T0


def test_schema_created(engine):
    tables = set(inspect(engine).get_table_names())
    assert {"stations", "station_status", "station_metrics"} <= tables


def test_empty_database_by_default(db_session):
    assert db_session.scalar(select(func.count()).select_from(Station)) == 0


def test_seed_row_counts(seeded_db):
    count = lambda model: seeded_db.scalar(select(func.count()).select_from(model))
    assert count(Station) == len(SEED_STATIONS)
    assert count(StationStatus) == len(SEED_STATUS)
    assert count(StationMetrics) == len(SEED_METRICS)


def test_unique_station_timestamp_enforced(seeded_db):
    seeded_db.add(StationStatus(uid=1, timestamp=T0, bikes=1, free_racks=1))
    with pytest.raises(IntegrityError):
        seeded_db.commit()


def test_foreign_key_enforced(db_session):
    db_session.add(StationStatus(uid=999, timestamp=T0, bikes=1, free_racks=1))
    with pytest.raises(IntegrityError):
        db_session.commit()


def test_client_uses_test_database(client, seeded_db):
    response = client.get("/stations")
    assert response.status_code == 200
    assert [s["uid"] for s in response.json()] == [s[0] for s in SEED_STATIONS]


def test_client_with_empty_database(client):
    assert client.get("/stations").status_code == 404
