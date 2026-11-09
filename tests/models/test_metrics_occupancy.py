"""Average occupancy KPI (issue #1), against the SQLite test DB.

Occupancy is bikes / (bikes + free_racks); Station.bike_racks plays no role,
so stations without bike_racks must still be counted.
"""
import pytest

from src.nextbike_prediction.models.metrics import get_avg_occupancy
from tests.conftest import T0, T1


def test_avg_occupancy_uses_free_racks(seeded_db):
    # T1: 6/10=60, 1/8=12.5, 0/12=0; station 4 (0 bikes, 0 free racks) is excluded.
    assert get_avg_occupancy(seeded_db, T1) == pytest.approx((60 + 12.5 + 0) / 3)


def test_avg_occupancy_includes_stations_without_bike_racks(seeded_db):
    # T0: 4/10=40, 0/8=0, 6/12=50, station 4 (bike_racks=None) 2/2=100.
    assert get_avg_occupancy(seeded_db, T0) == pytest.approx((40 + 0 + 50 + 100) / 4)


def test_avg_occupancy_none_without_data(db_session):
    assert get_avg_occupancy(db_session, T1) is None


def test_status_avg_occupancy_matches_stations_mean(seeded_db, client):
    status = client.get("/status").json()
    stations = client.get("/stations").json()
    values = [s["occupancy_pct"] for s in stations if s["occupancy_pct"] is not None]

    assert status["avg_occupancy"] == pytest.approx(sum(values) / len(values), abs=0.1)
    assert status["avg_occupancy_delta"] == pytest.approx(24.17 - 47.5, abs=0.1)
