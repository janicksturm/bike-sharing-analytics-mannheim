import pytest
import pandas as pd
import numpy as np

from script.services.location_service import LocationService


@pytest.fixture
def dummy_location_df():
    data = {
        "snapshot_time": [
            pd.Timestamp("2026-07-18 12:00:00"),
            pd.Timestamp("2026-07-18 13:00:00"),
            pd.Timestamp("2026-07-18 13:00:00"),
            pd.Timestamp("2026-07-18 13:00:00"),
        ],
        "uid": [1, 2, 1, 3],
        "name": ["Station A", "Station A", "Station A", "Station B"],
        "lat": [49.48, 49.48, 49.48, 49.49],
        "lng": [8.46, 8.46, 8.46, 8.47],
        "bikes": [5, 10, 29, 0],
        "free_racks": [10, 5, 0, 15],
        "occupancy_pct": [33.3, 66.666, 100.0, np.nan],
        "bikes_available_to_rent": [5, 10, 29, np.nan],
        "status": ["Available", "Available", "Availble", "Empty"]
    }
    return pd.DataFrame(data)


def test_filters_latest_snapshot_and_drops_duplicates(dummy_location_df):
    service = LocationService(dummy_location_df)
    stations = service.get_stations()

    assert len(stations) == 3
    
    station_1 = stations[stations.index(next(s for s in stations if s["uid"] == 1))]
    
    assert station_1["bikes"] == 29
    assert station_1["name"] == "Station A"


def test_handles_nans_and_casts_types_correctly(dummy_location_df):
    service = LocationService(dummy_location_df)
    stations = service.get_stations()
    
    station_2 = stations[stations.index(next(s for s in stations if s["uid"] == 2))]

    assert station_2["occupancy_pct"] == 66.7
    assert station_2["bikes_available_to_rent"] == 10

    assert type(station_2["uid"]) is int
    assert type(station_2["bikes"]) is int
    assert type(station_2["free_racks"]) is int
    assert type(station_2["bikes_available_to_rent"]) is int
    assert type(station_2["occupancy_pct"]) is float