from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class ExperimentSession(Base):
    __tablename__ = "experiment_sessions"

    id: Mapped[int] = mapped_column(primary_key=True)
    module: Mapped[str] = mapped_column(String(80), default="frog_rectus")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    observations: Mapped[list["Observation"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("experiment_sessions.id", ondelete="CASCADE"))
    drug: Mapped[str] = mapped_column(String(80))
    concentration_molar: Mapped[float] = mapped_column(Float)
    response_pct: Mapped[float] = mapped_column(Float)
    peak_height_mm: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    session: Mapped[ExperimentSession] = relationship(back_populates="observations")


class BioassayUnknown(Base):
    """Teacher-configured ACh stock; never returned in student API responses."""

    __tablename__ = "bioassay_unknowns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    code: Mapped[str] = mapped_column(String(24), unique=True, index=True)
    stock_concentration_um: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

