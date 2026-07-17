import pytest
import pandas as pd
from script.models.preprocessing import load_all_snapshots, features


@pytest.fixture
def raw_station_data():
    return pd.DataFrame({
        "uid": [339462, 660945, 339343],
        "bikes": [4, 0, 18],
        "free_racks": [4, 8, 0]
    })

def test_dataframe_header():
    expected_columns = [
        'snapshot_time', 'uid', 'lat', 'lng', 'name', 'number', 
        'bikes', 'bikes_available_to_rent', 'bike_racks', 'free_racks', 
        'total_capacity', 'occupancy_pct', 'status', 'bike_delta', 'demand_score'
    ]

    df = load_all_snapshots()

    assert df.columns.to_list() == expected_columns


def test_features_addition(raw_station_data):

    result_df = features(raw_station_data)
    
    assert "total_capacity" in result_df.columns
    assert "status" in result_df.columns
    assert "demand_score" in result_df.columns
    

    assert result_df.loc[0, "status"] == "Available"
    assert result_df.loc[1, "status"] == "Empty"