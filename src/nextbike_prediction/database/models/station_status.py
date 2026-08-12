from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class StationStatus(Base):
    __tablename__ = "station_status"

    id: Mapped[int] = mapped_column(primary_key=True)
    uid: Mapped[int] = mapped_column(ForeignKey("stations.uid"), nullable=False )
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    bikes: Mapped[int] = mapped_column(Integer, nullable=False)
    free_racks: Mapped[int] = mapped_column(Integer,nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "uid", 
            "timestamp", 
            name="unique_station_timestamp"
        ),
    )