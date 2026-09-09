from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.scenario import MONEY, RATE


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    amount_today: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    at_age: Mapped[int] = mapped_column(Integer, nullable=False)
    inflation: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("0"))
    recurrence: Mapped[str] = mapped_column(String(20), nullable=False, default="once")
    recurrence_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    duration_years: Mapped[int | None] = mapped_column(Integer, nullable=True)

    scenario: Mapped["Scenario"] = relationship(back_populates="goals")
