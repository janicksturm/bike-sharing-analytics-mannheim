"""RecommendationService and POST /recommendations against the SQLite test DB."""
from datetime import timedelta

import pytest

from src.nextbike_prediction.api.schema.recommendation import RecommendationResponse
from src.nextbike_prediction.database.models.station_status import StationStatus
from src.nextbike_prediction.models.recommendations import SEARCH_METERS
from src.nextbike_prediction.services.recommendation_service import RecommendationService
from tests.conftest import T1

# Wasserturm (uid 1) location from the seed data
USER_LAT, USER_LNG = 49.4875, 8.4660


def recommend(db, **kwargs):
    return RecommendationService(db).get_recommendations_for_location(USER_LAT, USER_LNG, **kwargs)


def test_ranks_seeded_stations(seeded_db):
    recs = recommend(seeded_db)["recommendations"]
    # At T1 only Wasserturm (6 bikes) and Paradeplatz (1 bike) have bikes
    assert [r["uid"] for r in recs] == [1, 2]
    assert [r["rank"] for r in recs] == [1, 2]


def test_output_values(seeded_db):
    recs = recommend(seeded_db)["recommendations"]
    first = recs[0]
    assert first["distance_meters"] == 0.0
    assert first["occupancy_pct"] == 60.0
    assert first["demand_score"] is None      # no snapshot in the 60–90 min window
    assert first["empty_rate"] == 0.0         # overall fallback (slot too sparse), in percent
    assert recs[1]["empty_rate"] == 50.0      # 0.5 -> 50 %
    RecommendationResponse.model_validate({"recommendations": recs, "search_radius_meters": 800})


def test_uses_time_slot_empty_rate(seeded_db):
    # Paradeplatz (uid 2) was empty at 10:xx on 4 earlier Saturdays -> slot rate 1.0
    # instead of its overall rate 0.5 (T1 is Saturday 10:30)
    for weeks in range(1, 5):
        seeded_db.add(StationStatus(uid=2, timestamp=T1 - timedelta(weeks=weeks), bikes=0, free_racks=8))
    seeded_db.commit()

    recs = {r["uid"]: r for r in recommend(seeded_db)["recommendations"]}
    # Slot for uid 2 at T1: 4 empty + T0 (empty) + T1 (1 bike) -> 5/6
    assert recs[2]["empty_rate"] == pytest.approx(83.3)
    assert recs[1]["empty_rate"] == 0.0  # still sparse -> overall fallback


def test_exclude_uid(seeded_db):
    recs = recommend(seeded_db, exclude_uid=1)["recommendations"]
    assert [r["uid"] for r in recs] == [2]


def test_search_radius_default(seeded_db):
    assert recommend(seeded_db)["search_radius_meters"] == SEARCH_METERS[0]


def test_search_radius_widens(seeded_db):
    # ~1.1 km north of Wasserturm: nothing within 800 m,
    # Wasserturm (~1.1 km) and Paradeplatz (~1.2 km) within 1500 m
    result = RecommendationService(seeded_db).get_recommendations_for_location(49.4975, 8.4660)
    assert result["search_radius_meters"] == 1500
    assert [r["uid"] for r in result["recommendations"]] == [1, 2]
    assert all(800 < r["distance_meters"] <= 1500 for r in result["recommendations"])


def test_empty_database(db_session):
    assert recommend(db_session) == {
        "recommendations": [],
        "search_radius_meters": SEARCH_METERS[-1],
    }


def test_endpoint(client, seeded_db):
    response = client.post("/recommendations", json={"lat": USER_LAT, "lng": USER_LNG})
    assert response.status_code == 200
    body = response.json()
    assert [r["uid"] for r in body["recommendations"]] == [1, 2]
    assert body["search_radius_meters"] == 800
