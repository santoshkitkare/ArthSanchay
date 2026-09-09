from decimal import Decimal
from typing import Literal

from pydantic import BaseModel

from app.schemas.scenario import DependentIn, GoalIn, IncomeStreamIn, ScenarioInputsIn

SolverTarget = Literal["required_corpus", "required_contribution", "longevity"]


class ProjectionOverrides(BaseModel):
    """Body for POST .../project — a transient what-if. Any field present overrides the saved
    scenario for this call only; nothing is persisted (§7, §8.3's what-if slider strip).
    """
    inputs: dict = {}
    dependents: list[DependentIn] | None = None
    goals: list[GoalIn] | None = None
    income_streams: list[IncomeStreamIn] | None = None


class AnonymousProjectionRequest(BaseModel):
    """Body for POST /api/project/anonymous — a full, self-contained input set, no scenario."""
    inputs: ScenarioInputsIn
    dependents: list[DependentIn] = []
    goals: list[GoalIn] = []
    income_streams: list[IncomeStreamIn] = []


class RowOut(BaseModel):
    t: int
    year: int
    age: int
    month: int
    corpus_start: Decimal
    inflow_contribution: Decimal
    inflow_income: Decimal
    household: Decimal
    medical: Decimal
    school: Decimal
    graduation: Decimal
    marriage: Decimal
    custom: Decimal
    outflow_total: Decimal
    investment_return: Decimal
    corpus_end: Decimal
    corpus_end_today_rupees: Decimal
    shortfall: Decimal
    events: list[str]


class SummaryOut(BaseModel):
    verdict: Literal["sustainable", "shortfall"]
    corpus_at_retirement: Decimal
    peak_corpus: Decimal
    peak_age: int
    exhaustion_age: int | None
    years_short: int
    terminal_corpus: Decimal
    unfunded_shortfall_nominal: Decimal
    unfunded_shortfall_today: Decimal
    total_withdrawals: Decimal
    total_contributions: Decimal
    total_return: Decimal
    first_year_withdrawal_rate: Decimal


class ProjectionMeta(BaseModel):
    plan_start_year: int
    months: int
    current_age: int
    retirement_age: int
    life_expectancy: int


class ProjectionOut(BaseModel):
    mode: Literal["monthly", "annual_parity"]
    meta: ProjectionMeta
    summary: SummaryOut
    rows: list[RowOut]


class SolveRequest(BaseModel):
    target: SolverTarget
    desired_legacy: Decimal = Decimal("0")


class SolveOut(BaseModel):
    target: SolverTarget
    feasible: bool
    value: Decimal | None
    value_today_rupees: Decimal | None
    gap_vs_current: Decimal | None
    message: str
    iterations: int
