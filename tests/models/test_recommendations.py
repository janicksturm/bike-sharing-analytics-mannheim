import pandas as pd

from script.models.recommendations import score_stations_for_user

latest_data = pd.DataFrame({
    "uid": [1, 2, 3, 4, 5, 6],
    "name": [
        "Lindenhof",
        "Neckarstadt",
        "Theresienkrankenhaus",
        "G7",
        "L1 Schloss",
        "MVV Hochhaus"
    ],
    "lat": [
        49.477082,
        49.497070,
        49.489559,
        49.491183,
        49.484705,
        49.494114
    ],
    "lng": [
        8.463662,
        8.473044,
        8.480297,
        8.462391,
        8.463544,
        8.467600
    ],
    "bikes": [6, 28, 0, 4, 0, 2],
    "demand_score": [-1, 3, 0, -2, 0, 1]
})

empty_rates = pd.DataFrame({
    "uid": [1,2,3,4,5,6],
    "empty_rate":[
        0.10,
        0.45,
        0.70,
        0.15,
        0.80,
        0.30
    ]
})

user_lat = 49.4875
user_lng = 8.4660


def test_only_stations_with_bikes_are_returned():

    result = score_stations_for_user(
        latest_data,
        empty_rates,
        user_lat,
        user_lng
    )

    assert "Theresienkrankenhaus" not in result["name"].values
    assert "L1 Schloss" not in result["name"].values

def test_recommendation_score_exists():

    result = score_stations_for_user(
        latest_data,
        empty_rates,
        user_lat,
        user_lng
    )

    assert "recommendation_score" in result.columns
    assert result["recommendation_score"].notna().all()

def test_station_with_many_bikes_scores_higher():

    result = score_stations_for_user(
        latest_data,
        empty_rates,
        user_lat,
        user_lng
    )

    neckarstadt = result[result["name"]=="Neckarstadt"]["recommendation_score"].iloc[0]
    lindenhof = result[result["name"]=="Lindenhof"]["recommendation_score"].iloc[0]

    assert neckarstadt > lindenhof

def test_results_are_sorted():

    result = score_stations_for_user(
        latest_data,
        empty_rates,
        user_lat,
        user_lng
    )

    assert result["recommendation_score"].is_monotonic_decreasing

def test_top_n():

    result = score_stations_for_user(
        latest_data,
        empty_rates,
        user_lat,
        user_lng,
        top_n=3
    )

    assert len(result) == 3

def test_score_is_between_0_and_1():
    result = score_stations_for_user(
        latest_data, empty_rates, user_lat, user_lng
    )

    assert (result["recommendation_score"] >= 0).all(), f"Score less than 0 found: {result['recommendation_score'].min()}"
    assert (result["recommendation_score"] <= 1).all(), f"Score greater than 1 found: {result['recommendation_score'].max()}"


def test_single_station_gets_balanced_score():
    data = pd.DataFrame({
        "uid": [99],
        "name": ["Solo"],
        "lat": [49.490],
        "lng": [8.465],
        "bikes": [5],
        "demand_score": [0],
    })
    rates = pd.DataFrame({"uid": [99], "empty_rate": [0.2]})

    result = score_stations_for_user(data, rates, user_lat, user_lng)
    score = result["recommendation_score"].iloc[0]

    assert abs(score - 0.5) < 0.01, f"Station should have a balanced score of ~0.5, but got {score}"


def test_empty_rate_affects_ranking():
    data = pd.DataFrame({
        "uid": [20, 21],
        "name": ["Reliable", "Unreliable"],
        "lat": [49.488, 49.488],
        "lng": [8.466, 8.466],
        "bikes": [10, 10],
        "demand_score": [0, 0],
    })
    rates = pd.DataFrame({"uid": [20, 21], "empty_rate": [0.05, 0.90]})

    result = score_stations_for_user(data, rates, user_lat, user_lng)
    reliable = result[result["name"] == "Reliable"]["recommendation_score"].iloc[0]
    unreliable = result[result["name"] == "Unreliable"]["recommendation_score"].iloc[0]

    assert reliable > unreliable, \
        f"Reliable ({reliable}) should score higher than Unreliable ({unreliable})"


def test_close_station_beats_far_with_same_bikes():
    data = pd.DataFrame({
        "uid": [30, 31],
        "name": ["Close", "Far"],
        "lat": [49.488, 49.520],
        "lng": [8.466, 8.500],
        "bikes": [10, 10],
        "demand_score": [0, 0],
    })
    rates = pd.DataFrame({"uid": [30, 31], "empty_rate": [0.1, 0.1]})

    result = score_stations_for_user(data, rates, user_lat, user_lng)
    close = result[result["name"] == "Close"]["recommendation_score"].iloc[0]
    far = result[result["name"] == "Far"]["recommendation_score"].iloc[0]

    assert close > far, f"Close ({close}) should score higher than Far ({far})"
