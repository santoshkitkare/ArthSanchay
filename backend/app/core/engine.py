"""The retirement projection engine.

This module is the authoritative implementation of PRD.md §5 (Calculation Specification). It is a
pure function of its input (FR-ENG-12): no database access, no I/O, no clock reads, so it can be
unit-tested, reused by the solvers in `core.solver`, and called identically from the API layer.

Two modes are supported (FR-ENG-2):

- ``annual_parity`` — reproduces the source workbook's annual, begin-of-year-withdrawal arithmetic
  exactly (§5.4). This is what `tests/test_engine_parity.py` reconciles against the workbook's own
  cached values.
- ``monthly`` — the default (§5.5): one step per month, recurring costs spread evenly across the
  twelve months of their plan year, lump-sum goals landing in the first month of their plan year.

All money is `decimal.Decimal` (NFR-3) and rates convert geometrically, never by simple division
(FR-ENG-3). The corpus is floored at zero the moment it is exhausted and never earns a return
again (FR-ENG-5) — this is the fix for the workbook's defect D1, where a negative balance kept
compounding to a fictitious −₹17.34 crore.

One extension beyond the literal workbook formulas: the workbook has no income or contribution of
any kind (defect D3), so §5.2 introduces `SIP(y)` and `INC_k(y)`. To keep both modes able to use
them symmetrically, the annual-mode withdrawal in `annual_parity` is defined here as
``W(y) − 12 × inflow(y)`` rather than the literal `W(y)` alone. When `inflow(y)` is zero — true for
every input the workbook itself ever held — this is identical to the workbook's formula, so the
golden parity test is unaffected.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, getcontext
from typing import Literal

getcontext().prec = 28

ZERO = Decimal("0")
ONE = Decimal("1")
TWELVE = Decimal("12")

EngineMode = Literal["monthly", "annual_parity"]
GoalRecurrence = Literal["once", "annual", "every_n_years"]


# --------------------------------------------------------------------------------------
# Input model
# --------------------------------------------------------------------------------------


@dataclass
class Dependent:
    label: str
    current_age: int
    school_fee_today: Decimal = ZERO
    school_fee_hike: Decimal = ZERO  # fraction, e.g. Decimal("0.25")
    school_fee_hike_frequency: int = 2
    school_end_age: int = 18
    graduation_cost_today: Decimal = ZERO
    graduation_inflation: Decimal = ZERO
    graduation_start_age: int = 18
    graduation_duration: int = 4
    inflate_graduation_instalments: bool = True
    marriage_cost_today: Decimal = ZERO
    marriage_inflation: Decimal = ZERO
    marriage_age: int | None = None
    fund_school_from_corpus_pre_retirement: bool = True


@dataclass
class Goal:
    label: str
    amount_today: Decimal
    at_age: int
    inflation: Decimal = ZERO
    recurrence: GoalRecurrence = "once"
    recurrence_years: int | None = None  # required for "every_n_years"
    duration_years: int | None = None  # None => until life expectancy (annual/every_n_years)


@dataclass
class IncomeStream:
    label: str
    monthly_amount_today: Decimal
    start_age: int
    end_age: int | None = None  # None => life expectancy
    annual_escalation: Decimal = ZERO


@dataclass
class ScenarioInput:
    current_age: int
    retirement_age: int
    life_expectancy: int
    current_corpus: Decimal
    annual_expense_today: Decimal
    expense_inflation: Decimal
    pre_retirement_return: Decimal
    post_retirement_return: Decimal
    monthly_contribution: Decimal = ZERO
    contribution_stepup: Decimal = ZERO
    contributions_stop_age: int | None = None  # resolved by caller to retirement_age if None
    medical_expense_today: Decimal = ZERO
    medical_inflation: Decimal = ZERO
    charge_household_expense_pre_retirement: bool = False
    post_retirement_expense_factor: Decimal = ONE
    engine_mode: EngineMode = "monthly"
    plan_start_year: int = 2026
    dependents: list[Dependent] = field(default_factory=list)
    goals: list[Goal] = field(default_factory=list)
    income_streams: list[IncomeStream] = field(default_factory=list)

    @property
    def plan_years(self) -> int:
        """Number of plan years, ages current_age..life_expectancy inclusive (FR-ENG-7)."""
        return self.life_expectancy - self.current_age + 1

    @property
    def resolved_contributions_stop_age(self) -> int:
        return (
            self.contributions_stop_age
            if self.contributions_stop_age is not None
            else self.retirement_age
        )


# --------------------------------------------------------------------------------------
# Annual cost formulas — PRD.md §5.2
# --------------------------------------------------------------------------------------


def _rate_pow(base: Decimal, exponent: int) -> Decimal:
    """Integer-exponent power, always exact for our precision."""
    return base**exponent


def household_expense(inp: ScenarioInput, y: int) -> Decimal:
    age = inp.current_age + y
    if age < inp.retirement_age and not inp.charge_household_expense_pre_retirement:
        return ZERO
    factor = inp.post_retirement_expense_factor if age >= inp.retirement_age else ONE
    return inp.annual_expense_today * _rate_pow(ONE + inp.expense_inflation, y) * factor


def medical_expense(inp: ScenarioInput, y: int) -> Decimal:
    if inp.medical_expense_today == ZERO:
        return ZERO
    return inp.medical_expense_today * _rate_pow(ONE + inp.medical_inflation, y)


def school_fee(dep: Dependent, current_age: int, y: int) -> Decimal:
    child_age = dep.current_age + y
    if child_age >= dep.school_end_age:
        return ZERO
    step = y // dep.school_fee_hike_frequency if dep.school_fee_hike_frequency > 0 else 0
    return dep.school_fee_today * _rate_pow(ONE + dep.school_fee_hike, step)


def graduation_cost(dep: Dependent, y: int) -> Decimal:
    child_age = dep.current_age + y
    g0 = dep.graduation_start_age
    n = dep.graduation_duration
    if n <= 0 or not (g0 <= child_age <= g0 + n - 1):
        return ZERO
    exponent = (child_age - dep.current_age) if dep.inflate_graduation_instalments else (g0 - dep.current_age)
    return dep.graduation_cost_today * _rate_pow(ONE + dep.graduation_inflation, exponent) / Decimal(n)


def marriage_cost(dep: Dependent, y: int) -> Decimal:
    if dep.marriage_age is None:
        return ZERO
    child_age = dep.current_age + y
    if child_age != dep.marriage_age:
        return ZERO
    exponent = dep.marriage_age - dep.current_age
    return dep.marriage_cost_today * _rate_pow(ONE + dep.marriage_inflation, exponent)


def _goal_years(goal: Goal, current_age: int, life_expectancy: int) -> list[int]:
    """Plan-year indices (0-based) in which this goal fires."""
    y0 = goal.at_age - current_age
    max_y = life_expectancy - current_age
    if y0 < 0 or y0 > max_y:
        return []
    if goal.recurrence == "once":
        return [y0]
    if goal.recurrence == "annual":
        last = y0 + goal.duration_years - 1 if goal.duration_years is not None else max_y
        return [y for y in range(y0, min(last, max_y) + 1)]
    if goal.recurrence == "every_n_years":
        step = goal.recurrence_years or 1
        last = y0 + goal.duration_years - 1 if goal.duration_years is not None else max_y
        return [y for y in range(y0, min(last, max_y) + 1, step)]
    return []


def goal_amount_for_year(goal: Goal, y: int) -> Decimal:
    return goal.amount_today * _rate_pow(ONE + goal.inflation, y)


def sip_amount(inp: ScenarioInput, y: int) -> Decimal:
    age = inp.current_age + y
    if age >= inp.resolved_contributions_stop_age:
        return ZERO
    return inp.monthly_contribution * _rate_pow(ONE + inp.contribution_stepup, y)


def income_amount(stream: IncomeStream, current_age: int, y: int) -> Decimal:
    age = current_age + y
    end_age = stream.end_age
    if age < stream.start_age or (end_age is not None and age > end_age):
        return ZERO
    return stream.monthly_amount_today * _rate_pow(ONE + stream.annual_escalation, y)


@dataclass
class YearCosts:
    household: Decimal
    medical: Decimal
    school: Decimal
    graduation: Decimal
    marriage: Decimal
    custom: Decimal
    events: list[str]
    inflow_contribution_monthly: Decimal
    inflow_income_monthly: Decimal

    @property
    def total_withdrawals(self) -> Decimal:
        return self.household + self.medical + self.school + self.graduation + self.marriage + self.custom

    @property
    def total_inflow_monthly(self) -> Decimal:
        return self.inflow_contribution_monthly + self.inflow_income_monthly


def year_costs(inp: ScenarioInput, y: int) -> YearCosts:
    hh = household_expense(inp, y)
    med = medical_expense(inp, y)
    school = graduation = marriage = ZERO
    events: list[str] = []
    for dep in inp.dependents:
        s = school_fee(dep, inp.current_age, y)
        g = graduation_cost(dep, y)
        m = marriage_cost(dep, y)
        school += s
        graduation += g
        if g > ZERO:
            events.append(f"Graduation instalment: {dep.label}")
        if m > ZERO:
            marriage += m
            events.append(f"Marriage: {dep.label}")

    custom = ZERO
    for goal in inp.goals:
        if y in _goal_years(goal, inp.current_age, inp.life_expectancy):
            amt = goal_amount_for_year(goal, y)
            custom += amt
            if amt > ZERO:
                events.append(f"Goal: {goal.label}")

    sip = sip_amount(inp, y)
    income_total = sum((income_amount(s, inp.current_age, y) for s in inp.income_streams), ZERO)

    return YearCosts(
        household=hh,
        medical=med,
        school=school,
        graduation=graduation,
        marriage=marriage,
        custom=custom,
        events=events,
        inflow_contribution_monthly=sip,
        inflow_income_monthly=income_total,
    )


# --------------------------------------------------------------------------------------
# Rate conversion — PRD.md §5.3
# --------------------------------------------------------------------------------------


def monthly_rate(annual_rate: Decimal) -> Decimal:
    """Geometric conversion: r_m = (1 + r_a)^(1/12) − 1 (FR-ENG-3). Never divide by 12."""
    return (ONE + annual_rate) ** (ONE / TWELVE) - ONE


def rate_for_age(inp: ScenarioInput, age: int) -> Decimal:
    return inp.pre_retirement_return if age < inp.retirement_age else inp.post_retirement_return


# --------------------------------------------------------------------------------------
# Row / summary output shapes
# --------------------------------------------------------------------------------------


@dataclass
class Row:
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


@dataclass
class Summary:
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


@dataclass
class ProjectionResult:
    mode: EngineMode
    rows: list[Row]
    summary: Summary


# --------------------------------------------------------------------------------------
# The engine
# --------------------------------------------------------------------------------------


def project(inp: ScenarioInput) -> ProjectionResult:
    if inp.engine_mode == "annual_parity":
        return _project_annual(inp)
    return _project_monthly(inp)


def _deflate(value: Decimal, inp: ScenarioInput, y: int) -> Decimal:
    denom = _rate_pow(ONE + inp.expense_inflation, y)
    return value / denom if denom != ZERO else value


def _project_annual(inp: ScenarioInput) -> ProjectionResult:
    corpus = inp.current_corpus
    rows: list[Row] = []
    total_shortfall = ZERO
    total_shortfall_today = ZERO
    total_withdrawals = ZERO
    total_contributions = ZERO
    total_return = ZERO
    exhaustion_age: int | None = None
    corpus_at_retirement: Decimal | None = None
    peak_corpus = corpus
    peak_age = inp.current_age

    for y in range(inp.plan_years):
        age = inp.current_age + y
        costs = year_costs(inp, y)
        annual_inflow = (costs.inflow_contribution_monthly + costs.inflow_income_monthly) * TWELVE
        net_withdrawal = costs.total_withdrawals - annual_inflow

        if age == inp.retirement_age and corpus_at_retirement is None:
            corpus_at_retirement = corpus

        after = corpus - net_withdrawal
        shortfall = ZERO
        if after < ZERO:
            shortfall = -after
            after = ZERO
            if exhaustion_age is None:
                exhaustion_age = age

        rate = rate_for_age(inp, age)
        ret = after * rate
        corpus_end = after + ret

        rows.append(
            Row(
                t=y,
                year=inp.plan_start_year + y,
                age=age,
                month=0,
                corpus_start=corpus,
                inflow_contribution=costs.inflow_contribution_monthly * TWELVE,
                inflow_income=costs.inflow_income_monthly * TWELVE,
                household=costs.household,
                medical=costs.medical,
                school=costs.school,
                graduation=costs.graduation,
                marriage=costs.marriage,
                custom=costs.custom,
                outflow_total=costs.total_withdrawals,
                investment_return=ret,
                corpus_end=corpus_end,
                corpus_end_today_rupees=_deflate(corpus_end, inp, y),
                shortfall=shortfall,
                events=costs.events,
            )
        )

        total_shortfall += shortfall
        total_shortfall_today += _deflate(shortfall, inp, y)
        total_withdrawals += costs.total_withdrawals
        total_contributions += annual_inflow
        total_return += ret
        if corpus_end > peak_corpus:
            peak_corpus, peak_age = corpus_end, age

        corpus = corpus_end

    if corpus_at_retirement is None:
        corpus_at_retirement = inp.current_corpus

    summary = _build_summary(
        inp,
        rows,
        corpus_at_retirement,
        peak_corpus,
        peak_age,
        exhaustion_age,
        corpus,
        total_shortfall,
        total_shortfall_today,
        total_withdrawals,
        total_contributions,
        total_return,
    )
    return ProjectionResult(mode="annual_parity", rows=rows, summary=summary)


def _project_monthly(inp: ScenarioInput) -> ProjectionResult:
    corpus = inp.current_corpus
    rows: list[Row] = []
    total_shortfall = ZERO
    total_shortfall_today = ZERO
    total_withdrawals = ZERO
    total_contributions = ZERO
    total_return = ZERO
    exhaustion_age: int | None = None
    corpus_at_retirement: Decimal | None = None
    peak_corpus = corpus
    peak_age = inp.current_age

    for y in range(inp.plan_years):
        age = inp.current_age + y
        costs = year_costs(inp, y)
        recurring = (costs.household + costs.medical + costs.school) / TWELVE
        lump = costs.graduation + costs.marriage + costs.custom
        rate_m = monthly_rate(rate_for_age(inp, age))

        if age == inp.retirement_age and corpus_at_retirement is None:
            corpus_at_retirement = corpus

        for m in range(12):
            t = y * 12 + m
            month_outflow = recurring + (lump if m == 0 else ZERO)
            month_inflow = costs.total_inflow_monthly
            net = month_outflow - month_inflow

            after = corpus - net
            shortfall = ZERO
            if after < ZERO:
                shortfall = -after
                after = ZERO
                if exhaustion_age is None:
                    exhaustion_age = age

            ret = after * rate_m
            corpus_end = after + ret

            rows.append(
                Row(
                    t=t,
                    year=inp.plan_start_year + y,
                    age=age,
                    month=m,
                    corpus_start=corpus,
                    inflow_contribution=costs.inflow_contribution_monthly,
                    inflow_income=costs.inflow_income_monthly,
                    household=costs.household / TWELVE,
                    medical=costs.medical / TWELVE,
                    school=costs.school / TWELVE,
                    graduation=costs.graduation if m == 0 else ZERO,
                    marriage=costs.marriage if m == 0 else ZERO,
                    custom=costs.custom if m == 0 else ZERO,
                    outflow_total=month_outflow,
                    investment_return=ret,
                    corpus_end=corpus_end,
                    corpus_end_today_rupees=_deflate(corpus_end, inp, y),
                    shortfall=shortfall,
                    events=costs.events if m == 0 else [],
                )
            )

            total_shortfall += shortfall
            total_shortfall_today += _deflate(shortfall, inp, y)
            total_withdrawals += month_outflow
            total_contributions += month_inflow
            total_return += ret
            if corpus_end > peak_corpus:
                peak_corpus, peak_age = corpus_end, age

            corpus = corpus_end

    if corpus_at_retirement is None:
        corpus_at_retirement = inp.current_corpus

    summary = _build_summary(
        inp,
        rows,
        corpus_at_retirement,
        peak_corpus,
        peak_age,
        exhaustion_age,
        corpus,
        total_shortfall,
        total_shortfall_today,
        total_withdrawals,
        total_contributions,
        total_return,
    )
    return ProjectionResult(mode="monthly", rows=rows, summary=summary)


def _build_summary(
    inp: ScenarioInput,
    rows: list[Row],
    corpus_at_retirement: Decimal,
    peak_corpus: Decimal,
    peak_age: int,
    exhaustion_age: int | None,
    terminal_corpus: Decimal,
    total_shortfall: Decimal,
    total_shortfall_today: Decimal,
    total_withdrawals: Decimal,
    total_contributions: Decimal,
    total_return: Decimal,
) -> Summary:
    # First-year-of-retirement withdrawal rate (FR-VIZ-6): sum that year's outflow / corpus at retirement.
    ret_year_withdrawal = ZERO
    for r in rows:
        if r.age == inp.retirement_age:
            ret_year_withdrawal += r.outflow_total
    wd_rate = (ret_year_withdrawal / corpus_at_retirement) if corpus_at_retirement > ZERO else ZERO

    years_short = (inp.life_expectancy - exhaustion_age) if exhaustion_age is not None else 0

    return Summary(
        verdict="shortfall" if exhaustion_age is not None else "sustainable",
        corpus_at_retirement=corpus_at_retirement,
        peak_corpus=peak_corpus,
        peak_age=peak_age,
        exhaustion_age=exhaustion_age,
        years_short=years_short,
        terminal_corpus=terminal_corpus,
        unfunded_shortfall_nominal=total_shortfall,
        unfunded_shortfall_today=total_shortfall_today,
        total_withdrawals=total_withdrawals,
        total_contributions=total_contributions,
        total_return=total_return,
        first_year_withdrawal_rate=wd_rate,
    )
