from script.models.preprocessing import load_all_snapshots

def test_dataframe_header():
    expected_columns = [
        'snapshot_time', 'uid', 'lat', 'lng', 'name', 'number', 
        'bikes', 'bikes_available_to_rent', 'bike_racks', 'free_racks', 
        'total_capacity', 'occupancy_pct', 'status', 'bike_delta', 'demand_score'
    ]

    df = load_all_snapshots()

    assert df.columns.to_list() == expected_columns