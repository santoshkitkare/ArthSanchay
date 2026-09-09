from __future__ import annotations

from decimal import Decimal

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.scenario import MONEY, RATE


class Dependent(Base):
    __tablename__ = "dependents"

    id: Mapped[int] = mapped_column(primary_key=True)
    scenario_id: Mapped[int] = mapped_column(ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False, index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    label: Mapped[str] = mapped_column(String(40), nullable=False)
    current_age: Mapped[int] = mapped_column(Integer, nullable=False)

    school_fee_today: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=Decimal("0"))
    school_fee_hike: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("0.25"))
    school_fee_hike_frequency: Mapped[int] = mapped_column(Integer, nullable=False, default=2)
    school_end_age: Mapped[int] = mapped_column(Integer, nullable=False, default=18)

    graduation_cost_today: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=Decimal("0"))
    graduation_inflation: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("0.07"))
    graduation_start_age: Mapped[int] = mapped_column(Integer, nullable=False, default=18)
    graduation_duration: Mapped[int] = mapped_column(Integer, nullable=False, default=4)
    inflate_graduation_instalments: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    marriage_cost_today: Mapped[Decimal] = mapped_column(MONEY, nullable=False, default=Decimal("0"))
    marriage_inflation: Mapped[Decimal] = mapped_column(RATE, nullable=False, default=Decimal("0.07"))
    marriage_age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    fund_school_from_corpus_pre_retirement: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    scenario: Mapped["Scenario"] = relationship(back_populates="dependents")
