from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

MONEY = Numeric(18, 2)
RATE = Numeric(9, 6)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Scenario(Base):
    __tablename__ = "scenarios"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_scenario_user_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="scenarios")
    inputs: Mapped["ScenarioInputs"] = relationship(
        back_populates="scenario", cascade="all, delete-orphan", uselist=False
    )
    dependents: Mapped[list["Dependent"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan", order_by="Dependent.sort_order"
    )
    goals: Mapped[list["Goal"]] = relationship(back_populates="scenario", cascade="all, delete-orphan")
    income_streams: Mapped[list["IncomeStream"]] = relationship(
        back_populates="scenario", cascade="all, delete-orphan"
    )


class ScenarioInputs(Base):
    """1:1 with Scenario. Sections A/B/C of PRD.md §4.3 — the scalar assumptions."""

    __tablename__ = "scenario_inputs"

    scenario_id: Mapped[int] = mapped_column(
        ForeignKey("scenarios.id", ondelete="CASCADE"), primary_key=True
    )

    # Section A — timeline
    current_age: Mapped[int] = mapped_column(Integer, nullable=False)
    retirement_age: Mapped[int] = mapped_column(Integer, nullable=False)
    life_expectancy: Mapped[int] = mapped_column(Integer, nullable=False)
    plan_start_year: Mapped[int] = mapped_column(Integer, nullable=False, default=2026)

    # Section B — money
    current_corpus: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    monthly_contribution: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=Decimal("0"))
    contribution_stepup: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("0"))
    contributions_stop_age: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pre_retirement_return: Mapped[Decimal] = mapped_column(RATE, nullable=False)
    post_retirement_return: Mapped[Decimal] = mapped_column(RATE, nullable=False)

    # Section C — living expenses
    annual_expense_today: Mapped[Decimal] = mapped_column(MONEY, nullable=False)
    expense_inflation: Mapped[Decimal] = mapped_column(RATE, nullable=False)
    charge_household_expense_pre_retirement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    medical_expense_today: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=Decimal("0"))
    medical_inflation: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("0.10"))
    post_retirement_expense_factor: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("1.0"))

    engine_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")

    scenario: Mapped["Scenario"] = relationship(back_populates="inputs")
