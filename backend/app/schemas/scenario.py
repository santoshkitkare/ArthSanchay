from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EngineMode = Literal["monthly", "annual_parity"]
GoalRecurrence = Literal["once", "annual", "every_n_years"]


# --------------------------------------------------------------------------------------
# Dependents / goals / income streams
# --------------------------------------------------------------------------------------


class DependentBase(BaseModel):
    label: str = Field(min_length=1, max_length=40)
    current_age: int = Field(ge=0, le=40)
    school_fee_today: Decimal = Field(ge=0, default=Decimal("0"))
    school_fee_hike: Decimal = Field(ge=0, le=Decimal("0.50"), default=Decimal("0.25"))
    school_fee_hike_frequency: int = Field(ge=1, le=10, default=2)
    school_end_age: int = Field(ge=10, le=30, default=18)
    graduation_cost_today: Decimal = Field(ge=0, default=Decimal("0"))
    graduation_inflation: Decimal = Field(ge=0, le=Decimal("0.20"), default=Decimal("0.07"))
    graduation_start_age: int = Field(ge=15, le=30, default=18)
    graduation_duration: int = Field(ge=1, le=8, default=4)
    inflate_graduation_instalments: bool = True
    marriage_cost_today: Decimal = Field(ge=0, default=Decimal("0"))
    marriage_inflation: Decimal = Field(ge=0, le=Decimal("0.20"), default=Decimal("0.07"))
    marriage_age: int | None = Field(default=None, ge=18, le=45)
    fund_school_from_corpus_pre_retirement: bool = True

    @model_validator(mode="after")
    def _marriage_after_current_age(self) -> "DependentBase":
        if self.marriage_age is not None and self.marriage_age < self.current_age:
            raise ValueError("marriage_age cannot be before the dependent's current age")
        return self


class DependentIn(DependentBase):
    pass


class DependentOut(DependentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class GoalBase(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    amount_today: Decimal = Field(ge=0)
    at_age: int = Field(ge=0, le=110)
    inflation: Decimal = Field(ge=0, le=Decimal("0.20"), default=Decimal("0"))
    recurrence: GoalRecurrence = "once"
    recurrence_years: int | None = Field(default=None, ge=1, le=20)
    duration_years: int | None = Field(default=None, ge=1, le=80)

    @model_validator(mode="after")
    def _recurrence_fields(self) -> "GoalBase":
        if self.recurrence == "every_n_years" and self.recurrence_years is None:
            raise ValueError("recurrence_years is required when recurrence is 'every_n_years'")
        return self


class GoalIn(GoalBase):
    pass


class GoalOut(GoalBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


class IncomeStreamBase(BaseModel):
    label: str = Field(min_length=1, max_length=80)
    monthly_amount_today: Decimal = Field(ge=0)
    start_age: int = Field(ge=0, le=110)
    end_age: int | None = Field(default=None, ge=0, le=110)
    annual_escalation: Decimal = Field(ge=0, le=Decimal("0.20"), default=Decimal("0"))

    @model_validator(mode="after")
    def _end_after_start(self) -> "IncomeStreamBase":
        if self.end_age is not None and self.end_age < self.start_age:
            raise ValueError("end_age cannot be before start_age")
        return self


class IncomeStreamIn(IncomeStreamBase):
    pass


class IncomeStreamOut(IncomeStreamBase):
    model_config = ConfigDict(from_attributes=True)
    id: int


# --------------------------------------------------------------------------------------
# Scalar scenario inputs (Sections A/B/C)
# --------------------------------------------------------------------------------------


class ScenarioInputsBase(BaseModel):
    current_age: int = Field(ge=18, le=75)
    retirement_age: int = Field(ge=18, le=110)
    life_expectancy: int = Field(ge=19, le=110)
    plan_start_year: int = Field(ge=1900, le=2200, default=2026)

    current_corpus: Decimal = Field(ge=0)
    monthly_contribution: Decimal = Field(ge=0, default=Decimal("0"))
    contribution_stepup: Decimal = Field(ge=0, le=Decimal("0.25"), default=Decimal("0"))
    contributions_stop_age: int | None = Field(default=None, ge=0, le=110)
    pre_retirement_return: Decimal = Field(ge=Decimal("-0.20"), le=Decimal("0.40"))
    post_retirement_return: Decimal = Field(ge=Decimal("-0.20"), le=Decimal("0.40"))

    annual_expense_today: Decimal = Field(ge=0)
    expense_inflation: Decimal = Field(ge=0, le=Decimal("0.20"))
    charge_household_expense_pre_retirement: bool = False
    medical_expense_today: Decimal = Field(ge=0, default=Decimal("0"))
    medical_inflation: Decimal = Field(ge=0, le=Decimal("0.25"), default=Decimal("0.10"))
    post_retirement_expense_factor: Decimal = Field(ge=Decimal("0.30"), le=Decimal("1.50"), default=Decimal("1.0"))

    engine_mode: EngineMode = "monthly"

    @model_validator(mode="after")
    def _age_ordering(self) -> "ScenarioInputsBase":
        if self.retirement_age < self.current_age:
            raise ValueError("retirement_age cannot be before current_age")
        if self.life_expectancy <= self.retirement_age:
            raise ValueError("life_expectancy must be after retirement_age")
        return self


class ScenarioInputsIn(ScenarioInputsBase):
    pass


class ScenarioInputsOut(ScenarioInputsBase):
    model_config = ConfigDict(from_attributes=True)


# --------------------------------------------------------------------------------------
# Scenario (composite)
# --------------------------------------------------------------------------------------


class ScenarioCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    inputs: ScenarioInputsIn | None = None
    dependents: list[DependentIn] | None = None
    goals: list[GoalIn] | None = None
    income_streams: list[IncomeStreamIn] | None = None


class ScenarioReplace(BaseModel):
    """PUT — full replace of a scenario's input set."""
    name: str = Field(min_length=1, max_length=120)
    inputs: ScenarioInputsIn
    dependents: list[DependentIn] = Field(default_factory=list)
    goals: list[GoalIn] = Field(default_factory=list)
    income_streams: list[IncomeStreamIn] = Field(default_factory=list)


class ScenarioPatch(BaseModel):
    """PATCH — partial update, used by the live what-if controls. Any field omitted is left
    unchanged; dependents/goals/income_streams, if provided, replace the full list (there is no
    partial-list patch semantics).
    """
    name: str | None = Field(default=None, min_length=1, max_length=120)
    inputs: dict = Field(default_factory=dict)  # validated field-by-field in the route
    dependents: list[DependentIn] | None = None
    goals: list[GoalIn] | None = None
    income_streams: list[IncomeStreamIn] | None = None


class ScenarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    inputs: ScenarioInputsOut
    dependents: list[DependentOut]
    goals: list[GoalOut]
    income_streams: list[IncomeStreamOut]


class ScenarioListItem(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    verdict: Literal["sustainable", "shortfall"]
    exhaustion_age: int | None
    years_short: int
