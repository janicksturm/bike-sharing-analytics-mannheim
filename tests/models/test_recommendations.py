import pandas as pd
import pytest

from script.models.recommendations import score_stations_for_user, _normalize

latest_data = pd.DataFrame({
    "uid": [1, 2, 3, 4, 5, 6],
    "name": ["Lindenhof", "Neckarstadt", "Theresienkrankenhaus", "G7", "L1 Schloss", "MVV Hochhaus"],
    "lat": [49.477082, 49.497070, 49.489559, 49.491183, 49.484705, 49.494114],
    "lng": [8.463662, 8.473044, 8.480297, 8.462391, 8.463544, 8.467600],
    "bikes": [6, 28, 0, 4, 0, 2],
    "demand_score": [-1, 3, 0, -2, 0, 1]
})

empty_rates = pd.DataFrame({
    "uid": [1, 2, 3, 4, 5, 6],
    "empty_rate": [0.10, 0.45, 0.70, 0.15, 0.80, 0.30]
})

USER_LAT = 49.4875
USER_LNG = 8.4660


def test_normalize_maps_min_max():
    result = _normalize(pd.Series([0, 50, 100]))
    assert result.iloc[0] == pytest.approx(0.0)
    assert result.iloc[1] == pytest.approx(0.5)
    assert result.iloc[2] == pytest.approx(1.0)

def test_normalize_equal_values():
    result = _normalize(pd.Series([7, 7, 7]))
    assert (result == 0.5).all()


def test_stations_without_bikes_filtered():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    assert "Theresienkrankenhaus" not in result["name"].values
    assert "L1 Schloss" not in result["name"].values


def test_results_are_sorted():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    assert result["recommendation_score"].is_monotonic_decreasing


def test_top_n():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG, top_n=3)
    assert len(result) == 3


def test_empty_input():
    result = score_stations_for_user(pd.DataFrame(), empty_rates, USER_LAT, USER_LNG)
    assert result.empty


def test_score_between_0_and_1():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    assert (result["recommendation_score"] >= 0).all()
    assert (result["recommendation_score"] <= 1).all()


def test_more_bikes_scores_higher():
    data = pd.DataFrame({
        "uid": [1, 2], "name": ["Many", "Few"],
        "lat": [49.488, 49.488], "lng": [8.466, 8.466],
        "bikes": [20, 3], "demand_score": [0, 0],
    })
    rates = pd.DataFrame({"uid": [1, 2], "empty_rate": [0.1, 0.1]})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Many"


def test_closer_station_scores_higher():
    data = pd.DataFrame({
        "uid": [1, 2], "name": ["Close", "Far"],
        "lat": [49.488, 49.520], "lng": [8.466, 8.500],
        "bikes": [10, 10], "demand_score": [0, 0],
    })
    rates = pd.DataFrame({"uid": [1, 2], "empty_rate": [0.1, 0.1]})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Close"


def test_lower_empty_rate_scores_higher():
    data = pd.DataFrame({
        "uid": [1, 2], "name": ["Reliable", "Unreliable"],
        "lat": [49.488, 49.488], "lng": [8.466, 8.466],
        "bikes": [10, 10], "demand_score": [0, 0],
    })
    rates = pd.DataFrame({"uid": [1, 2], "empty_rate": [0.05, 0.90]})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Reliable"


def test_positive_trend_scores_higher():
    data = pd.DataFrame({
        "uid": [1, 2], "name": ["Returning", "Leaving"],
        "lat": [49.488, 49.488], "lng": [8.466, 8.466],
        "bikes": [10, 10], "demand_score": [-3, 3],
    })
    rates = pd.DataFrame({"uid": [1, 2], "empty_rate": [0.1, 0.1]})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Returning"
