"""Shared pytest fixtures: an in-memory SQLite database that mirrors the
production PostgreSQL schema, plus a seeded dataset with known values.

Fixtures
--------
engine        fresh in-memory SQLite engine with all tables created (per test)
db_session    SQLAlchemy session bound to ``engine``
seeded_db     ``db_session`` pre-filled with SEED_* data below
client        FastAPI TestClient whose ``get_db`` dependency uses ``db_session``
"""
from collections.abc import Generator
from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.nextbike_prediction.api.app import app
from src.nextbike_prediction.api.dependencies import get_db
from src.nextbike_prediction.database.models.base import Base
from src.nextbike_prediction.database.models.station import Station
from src.nextbike_prediction.database.models.station_metrics import StationMetrics
from src.nextbike_prediction.database.models.station_status import StationStatus


T0 = datetime(2026, 11, 7, 10, 0)   # previous snapshot
T1 = datetime(2026, 11, 7, 10, 30)  # latest snapshot

SEED_STATIONS = [
    # uid, name, lat, lng, bike_racks
    (1, "Wasserturm", 49.4875, 8.4660, 10),
    (2, "Paradeplatz", 49.4870, 8.4650, 8),
    (3, "Schloss", 49.4840, 8.4620, 12),
    (4, "Hauptbahnhof", 49.4794, 8.4699, None),
]

SEED_STATUS = [
    # uid, timestamp, bikes, free_racks
    (1, T0, 4, 6),
    (2, T0, 0, 8),
    (3, T0, 6, 6),
    (4, T0, 2, 0),
    (1, T1, 6, 4),
    (2, T1, 1, 7),
    (3, T1, 0, 12),
    (4, T1, 0, 0),
]

SEED_METRICS = [
    # uid, timestamp, empty_rate (0..1), avg_bikes, avg_occupancy (%)
    (1, T1, 0.0, 5.0, 50.0),
    (2, T1, 0.5, 0.5, 6.25),
    (3, T1, 0.5, 3.0, 25.0),
    (4, T1, 0.5, 1.0, 100.0),
]


def seed_database(session: Session) -> None:
    """Insert the SEED_* rows into ``session`` and commit."""
    session.add_all(
        Station(uid=uid, name=name, lat=lat, lng=lng, bike_racks=racks)
        for uid, name, lat, lng, racks in SEED_STATIONS
    )
    session.flush()
    session.add_all(
        StationStatus(uid=uid, timestamp=ts, bikes=bikes, free_racks=free)
        for uid, ts, bikes, free in SEED_STATUS
    )
    session.add_all(
        StationMetrics(uid=uid, timestamp=ts, empty_rate=er, avg_bikes=ab, avg_occupancy=ao)
        for uid, ts, er, ab, ao in SEED_METRICS
    )
    session.commit()


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    # SQLite ignores FOREIGN KEY constraints unless explicitly enabled.
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    event.listen(engine, "connect", _enable_sqlite_foreign_keys)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Generator[Session, None, None]:
    TestSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with TestSession() as session:
        yield session


@pytest.fixture
def seeded_db(db_session: Session) -> Session:
    seed_database(db_session)
    return db_session


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    """TestClient backed by ``db_session``. Combine with ``seeded_db`` for data."""
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
