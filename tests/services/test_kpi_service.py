import pytest
import pandas as pd

from script.services.kpi_service import KpiService


@pytest.fixture
def df_multi():
    data = {
        "snapshot_time": [
            pd.Timestamp("2026-07-17 18:02:29"), pd.Timestamp("2026-07-17 10:11:43"),
            pd.Timestamp("2026-06-15 11:00:00"), pd.Timestamp("2026-05-10 08:23:40")
        ],
        "station_id": [1, 2, 1, 2],
        "bikes": [10, 0, 12, 5],
        "occupancy_pct": [50.0, 0.0, 60.0, 25.0]
    }
    return pd.DataFrame(data)

@pytest.fixture
def df_single():
    data = {
        "snapshot_time": [
            pd.Timestamp("2026-07-17 20:30:38")
        ],
        "station_id": [1],
        "bikes": [20],
        "occupancy_pct": [25.0]
    }
    return pd.DataFrame(data)


def test_get_status_multiple_snapshots(df_multi):
    service = KpiService(df_multi)
    result = service.get_status()

    assert result["snapshot_time"] == pd.Timestamp("2026-07-17 18:02:29").isoformat()

    assert result["total_bikes"]["value"] == 10
    assert result["total_bikes"]["delta"] == 10

    assert result["available_to_rent"]["value"] == 1
    assert result["available_to_rent"]["delta"] == 1

    assert result["empty_stations"]["value"] == 0
    assert result["empty_stations"]["delta"] == -1

    assert result["avg_occupancy"]["value"] == 50.0
    assert result["avg_occupancy"]["delta"] == 50.0


def test_get_status_single_snapshot(df_single):
    service = KpiService(df_single)
    result = service.get_status()

    assert result["total_bikes"]["value"] == 20
    assert result["total_bikes"]["delta"] is None
    
    assert result["available_to_rent"]["value"] == 1
    assert result["available_to_rent"]["delta"] is None

    assert result["empty_stations"]["value"] == 0
    assert result["empty_stations"]["delta"] is None

    assert result["avg_occupancy"]["value"] == 25.0
    assert result["avg_occupancy"]["delta"] is None