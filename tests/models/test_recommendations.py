import pandas as pd
import pytest

from script.models.recommendations import score_stations_for_user, _normalize

latest_data = pd.DataFrame({
    "uid": [1, 2, 3, 4, 5, 6],
    "name": ["Schloss", "Marktplatz", "Rathaus", "Paradeplatz", "Uni Mensa", "Wasserturm"],
    "lat": [49.4880, 49.4870, 49.4890, 49.4860, 49.4885, 49.4865],
    "lng": [8.4665, 8.4650, 8.4670, 8.4655, 8.4675, 8.4645],
    "bikes": [6, 12, 0, 4, 0, 2],
    "demand_score": [-1, 3, 0, -2, 0, 1],
})

empty_rates = pd.DataFrame({
    "uid": [1, 2, 3, 4, 5, 6],
    "empty_rate": [0.10, 0.45, 0.70, 0.15, 0.80, 0.30],
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
    # Rathaus (0 bikes) and Uni Mensa (0 bikes) must be excluded
    assert "Rathaus" not in result["name"].values
    assert "Uni Mensa" not in result["name"].values


def test_stations_beyond_800m_filtered():
    """Stations farther than 800 m from the user must be excluded."""
    data = pd.DataFrame({
        "uid": [1, 2],
        "name": ["Nearby", "TooFar"],
        "lat": [49.4880, 49.520],
        "lng": [8.4665, 8.500],
        "bikes": [5, 5],
        "demand_score": [0, 0],
    })
    rates = pd.DataFrame({"uid": [1, 2], "empty_rate": [0.1, 0.1]})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert "TooFar" not in result["name"].values
    assert "Nearby" in result["name"].values


# ── Sorting & top-n ──────────────────────────────────────────────────

def test_results_are_sorted():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    assert result["recommendation_score"].is_monotonic_decreasing


def test_top_n():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG, top_n=2)
    assert len(result) == 2


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
        "uid": [1, 2], "name": ["Close", "FartherButInRange"],
        "lat": [49.4878, 49.4920], "lng": [8.4662, 8.4700],
        "bikes": [10, 10], "demand_score": [0, 0],
    })
    rates = pd.DataFrame({"uid": [1, 2], "empty_rate": [0.1, 0.1]})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert len(result) == 2
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
