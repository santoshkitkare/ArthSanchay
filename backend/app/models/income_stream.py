from __future__ import annotations

from decimal import Decimal

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.scenario import MONEY, RATE


class IncomeStream(Base):
    __tablename__ = "income_streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    label: Mapped[str] = mapped_column(String(80), nullable=False)
    monthly_amount_today: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    start_age: Mapped[int] = mapped_column(Integer, nullable=False)
    end_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    annual_escalation: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("0"))

    scenario: Mapped["Scenario"] = relationship(back_populates="income_streams")
