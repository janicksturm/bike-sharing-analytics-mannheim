import pandas as pd
import pytest

from src.nextbike_prediction.models.recommendations import (
    SEARCH_METERS,
    recommend_stations,
    score_stations_for_user,
    trend_score,
)

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

# One degree of latitude is ~111 195 m (haversine with R = 6 371 000 m).
METERS_PER_DEG_LAT = 111_195


def make_stations(**columns) -> pd.DataFrame:
    """Build station data; unspecified columns default to same spot / 10 bikes / no trend."""
    n = len(next(iter(columns.values())))
    defaults = {
        "uid": list(range(1, n + 1)),
        "name": [f"S{i}" for i in range(1, n + 1)],
        "lat": [49.488] * n,
        "lng": [8.466] * n,
        "bikes": [10] * n,
        "demand_score": [0] * n,
    }
    defaults.update(columns)
    return pd.DataFrame(defaults)


def make_rates(values: list[float]) -> pd.DataFrame:
    return pd.DataFrame({"uid": list(range(1, len(values) + 1)), "empty_rate": values})


# ── trend_score ──────────────────────────────────────────────────────

def test_trend_score_neutral_for_zero_and_unknown():
    assert trend_score(pd.Series([0, None])).tolist() == pytest.approx([0.5, 0.5])


def test_trend_score_bounded_and_monotonic():
    result = trend_score(pd.Series([-100, -1, 0, 1, 100]))
    assert result.is_monotonic_increasing
    assert result.iloc[0] == pytest.approx(0.0, abs=1e-6)
    assert result.iloc[-1] == pytest.approx(1.0, abs=1e-6)


def test_trend_score_independent_of_other_stations():
    alone = trend_score(pd.Series([1])).iloc[0]
    with_others = trend_score(pd.Series([1, 0, -5])).iloc[0]
    assert alone == pytest.approx(with_others)


def test_one_bike_delta_has_small_effect():
    # +1 bike may shift the trend score by at most ~0.17 (of 1.0)
    assert trend_score(pd.Series([1])).iloc[0] - 0.5 < 0.17


def test_trend_score_keeps_index():
    assert list(trend_score(pd.Series([1, 2], index=[10, 20])).index) == [10, 20]


# ── Filtering ────────────────────────────────────────────────────────

def test_stations_without_bikes_filtered():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    # Rathaus (0 bikes) and Uni Mensa (0 bikes) must be excluded
    assert "Rathaus" not in result["name"].values
    assert "Uni Mensa" not in result["name"].values


def test_stations_beyond_800m_filtered():
    """Stations farther than 800 m from the user must be excluded."""
    data = make_stations(name=["Nearby", "TooFar"], lat=[49.4880, 49.520], lng=[8.4665, 8.500])
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert "TooFar" not in result["name"].values
    assert "Nearby" in result["name"].values


def test_distance_boundary_around_800m():
    data = make_stations(
        name=["790m", "810m"],
        lat=[USER_LAT + 790 / METERS_PER_DEG_LAT, USER_LAT + 810 / METERS_PER_DEG_LAT],
        lng=[USER_LNG, USER_LNG],
    )
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert list(result["name"]) == ["790m"]
    assert result.iloc[0]["distance_meters"] == pytest.approx(790, abs=1)


def test_exclude_uid():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG, exclude_uid=2)
    assert 2 not in result["uid"].values
    assert len(result) == 3  # 4 stations with bikes minus the excluded one


def test_no_station_with_bikes_returns_empty():
    data = make_stations(bikes=[0, 0])
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert result.empty


def test_all_stations_out_of_range_returns_empty():
    data = make_stations(lat=[49.60, 49.61])
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert result.empty


def test_empty_input():
    result = score_stations_for_user(pd.DataFrame(), empty_rates, USER_LAT, USER_LNG)
    assert result.empty


# ── Missing data handling ────────────────────────────────────────────

def test_missing_empty_rate_gets_median():
    data = make_stations(uid=[1, 2, 3])
    rates = pd.DataFrame({"uid": [1, 2], "empty_rate": [0.1, 0.5]})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert result.set_index("uid").loc[3, "empty_rate"] == pytest.approx(0.3)


def test_no_empty_rates_at_all_falls_back_to_zero():
    data = make_stations(uid=[1, 2])
    rates = pd.DataFrame(columns=["uid", "empty_rate"]).astype({"uid": int, "empty_rate": float})
    result = score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    assert (result["empty_rate"] == 0).all()


def test_nan_demand_score_treated_as_zero():
    data = make_stations(demand_score=[None, 0, 2])
    result = score_stations_for_user(data, make_rates([0.1] * 3), USER_LAT, USER_LNG)
    by_uid = result.set_index("uid")
    assert by_uid.loc[1, "demand_trend"] == 0
    assert by_uid.loc[1, "recommendation_score"] == pytest.approx(by_uid.loc[2, "recommendation_score"])


def test_input_frames_not_mutated():
    data = latest_data.copy()
    rates = empty_rates.copy()
    score_stations_for_user(data, rates, USER_LAT, USER_LNG)
    pd.testing.assert_frame_equal(data, latest_data)
    pd.testing.assert_frame_equal(rates, empty_rates)


# ── Sorting & top-n ──────────────────────────────────────────────────

def test_results_are_sorted():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    assert result["recommendation_score"].is_monotonic_decreasing


def test_top_n():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG, top_n=2)
    assert len(result) == 2


def test_default_top_n_is_five():
    data = make_stations(uid=list(range(1, 8)))
    result = score_stations_for_user(data, make_rates([0.1] * 7), USER_LAT, USER_LNG)
    assert len(result) == 5


def test_index_is_reset():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    assert list(result.index) == list(range(len(result)))


# ── Score values ─────────────────────────────────────────────────────

def test_score_between_0_and_1():
    result = score_stations_for_user(latest_data, empty_rates, USER_LAT, USER_LNG)
    assert (result["recommendation_score"] >= 0).all()
    assert (result["recommendation_score"] <= 1).all()


def test_known_score_for_single_station():
    """Pins the formula/weights: bikes=8, distance=0, empty_rate=0, single station.

    0.25 * (1 - e^-1)   bikes
    + 0.10 * e^0        reliability
    + 0.40 * e^0        distance
    + 0.25 * 0.5        trend (single value -> neutral 0.5)
    = 0.783030...
    """
    data = make_stations(lat=[USER_LAT], lng=[USER_LNG], bikes=[8])
    result = score_stations_for_user(data, make_rates([0.0]), USER_LAT, USER_LNG)
    assert result.iloc[0]["recommendation_score"] == pytest.approx(0.783030, abs=1e-6)


def test_more_bikes_scores_higher():
    data = make_stations(name=["Many", "Few"], bikes=[20, 3])
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Many"


def test_closer_station_scores_higher():
    data = make_stations(
        name=["Close", "FartherButInRange"], lat=[49.4878, 49.4920], lng=[8.4662, 8.4700]
    )
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert len(result) == 2
    assert result.iloc[0]["name"] == "Close"


def test_lower_empty_rate_scores_higher():
    data = make_stations(name=["Reliable", "Unreliable"])
    result = score_stations_for_user(data, make_rates([0.05, 0.90]), USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Reliable"


def test_positive_trend_scores_higher():
    # demand_score = curr - prev bikes: positive means bikes are being returned
    data = make_stations(name=["Returning", "Leaving"], demand_score=[3, -3])
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Returning"


# ── Trend must not dominate availability or distance (issue #10) ────

def test_small_trend_does_not_outweigh_large_availability_gap():
    data = make_stations(name=["OneBikeRising", "TwentyBikes"], bikes=[1, 20], demand_score=[1, 0])
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "TwentyBikes"


def test_small_trend_does_not_outweigh_700m_walk():
    data = make_stations(
        name=["Here", "700mRising"],
        lat=[USER_LAT, USER_LAT + 700 / METERS_PER_DEG_LAT],
        lng=[USER_LNG, USER_LNG],
        demand_score=[0, 1],
    )
    result = score_stations_for_user(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert result.iloc[0]["name"] == "Here"


# ── Expanding search radius (issue #10) ─────────────────────────────

def _lat_at(meters: float) -> float:
    return USER_LAT + meters / METERS_PER_DEG_LAT


def test_max_distance_is_configurable():
    data = make_stations(name=["1200m"], lat=[_lat_at(1200)], lng=[USER_LNG])
    assert score_stations_for_user(data, make_rates([0.1]), USER_LAT, USER_LNG).empty
    result = score_stations_for_user(data, make_rates([0.1]), USER_LAT, USER_LNG, max_distance_meters=1500)
    assert list(result["name"]) == ["1200m"]


def test_recommend_uses_first_radius_when_station_nearby():
    data = make_stations(name=["300m", "1200m"], lat=[_lat_at(300), _lat_at(1200)], lng=[USER_LNG] * 2)
    result, radius = recommend_stations(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG)
    assert radius == SEARCH_METERS[0]
    assert list(result["name"]) == ["300m"]  # the 1200 m station is not mixed in


def test_recommend_widens_radius_when_nothing_nearby():
    data = make_stations(
        name=["Empty300m", "Full1200m", "Full2500m"],
        lat=[_lat_at(m) for m in (300, 1200, 2500)],
        lng=[USER_LNG] * 3,
        bikes=[0, 5, 5],
    )
    result, radius = recommend_stations(data, make_rates([0.1] * 3), USER_LAT, USER_LNG)
    assert radius == 1500
    assert list(result["name"]) == ["Full1200m"]


def test_recommend_uses_largest_radius():
    data = make_stations(name=["2500m"], lat=[_lat_at(2500)], lng=[USER_LNG])
    result, radius = recommend_stations(data, make_rates([0.1]), USER_LAT, USER_LNG)
    assert radius == 3000
    assert list(result["name"]) == ["2500m"]


def test_recommend_returns_largest_radius_when_nothing_found():
    data = make_stations(lat=[49.70], lng=[8.70])
    result, radius = recommend_stations(data, make_rates([0.1]), USER_LAT, USER_LNG)
    assert result.empty
    assert radius == SEARCH_METERS[-1]


def test_recommend_empty_input():
    result, radius = recommend_stations(pd.DataFrame(), empty_rates, USER_LAT, USER_LNG)
    assert result.empty
    assert radius == SEARCH_METERS[-1]


def test_recommend_widens_when_only_nearby_station_is_excluded():
    data = make_stations(uid=[1, 2], lat=[_lat_at(100), _lat_at(1200)], lng=[USER_LNG] * 2)
    result, radius = recommend_stations(data, make_rates([0.1, 0.1]), USER_LAT, USER_LNG, exclude_uid=1)
    assert radius == 1500
    assert list(result["uid"]) == [2]


def test_recommend_passes_top_n():
    data = make_stations(uid=[1, 2, 3])
    result, _ = recommend_stations(data, make_rates([0.1] * 3), USER_LAT, USER_LNG, top_n=2)
    assert len(result) == 2


def test_radii_are_configurable():
    data = make_stations(lat=[_lat_at(1200)], lng=[USER_LNG])
    result, radius = recommend_stations(data, make_rates([0.1]), USER_LAT, USER_LNG, radii=(500, 1000))
    assert result.empty
    assert radius == 1000
