from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StationMetrics(Base):
    """Persisted per-station historical metrics, computed after every pipeline ingestion run"""

    __tablename__ = "station_metrics"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(ForeignKey("stations.uid"), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    empty_rate: Mapped[float] = mapped_column(Float, nullable=False)
    avg_bikes: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_occupancy: Mapped[float | None] = mapped_column(Float, nullable=True)
