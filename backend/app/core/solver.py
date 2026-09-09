"""Bisection solvers — PRD.md §5.8 (required corpus) and §5.9 (required contribution), plus a
thin longevity report for the third solve target (FR-SOL-3). Built directly on `core.engine`,
which stays a pure function throughout (FR-ENG-12).

Both bisections rely on a property validated by the engine's design: raising the starting corpus,
or raising the monthly contribution, never makes the outcome worse (PRD.md §11's property-based
test description). That monotonicity is what makes bisection valid here.
"""
from dataclasses import dataclass, replace
from decimal import Decimal

from app.core.engine import Dependent, ScenarioInput, project

ZERO = Decimal("0")
TOLERANCE = Decimal("100")
MAX_ITERATIONS = 80


@dataclass
class SolverResult:
    target: str
    feasible: bool
    value: Decimal | None
    value_today_rupees: Decimal | None
    gap_vs_current: Decimal | None
    message: str
    iterations: int


def _shift_dependents_to_age(dependents: list[Dependent], delta_years: int) -> list[Dependent]:
    return [replace(d, current_age=d.current_age + delta_years) for d in dependents]


def _deflator(inp: ScenarioInput, years_from_now: int) -> Decimal:
    return (Decimal(1) + inp.expense_inflation) ** years_from_now


def solve_required_corpus(inp: ScenarioInput, desired_legacy: Decimal = ZERO) -> SolverResult:
    """FR-SOL-1: the smallest corpus held at retirement that keeps the balance >= 0 (and >=
    desired_legacy at the end) through life expectancy.
    """
    delta = inp.retirement_age - inp.current_age
    retirement_scenario_base = replace(
        inp,
        current_age=inp.retirement_age,
        dependents=_shift_dependents_to_age(inp.dependents, delta),
    )

    # Establish the accumulation phase unchanged, to report the gap against what the plan
    # actually delivers at retirement (PRD.md §5.8 step 5).
    actual = project(inp)
    actual_corpus_at_retirement = actual.summary.corpus_at_retirement

    # Upper bound: 100x the lifetime withdrawals a huge corpus would never need to touch.
    probe = project(replace(retirement_scenario_base, current_corpus=Decimal("1e15")))
    upper_bound = probe.summary.total_withdrawals * 100
    if upper_bound <= ZERO:
        upper_bound = Decimal("100000000")

    def objective(x: Decimal) -> Decimal:
        result = project(replace(retirement_scenario_base, current_corpus=x))
        if result.summary.exhaustion_age is None:
            return result.summary.terminal_corpus - desired_legacy
        return -result.summary.unfunded_shortfall_nominal

    lo, hi = ZERO, upper_bound
    if objective(hi) < ZERO:
        return SolverResult(
            target="required_corpus",
            feasible=False,
            value=None,
            value_today_rupees=None,
            gap_vs_current=None,
            message=(
                "No corpus within a sane bound sustains this plan. Consider retiring later, "
                "reducing planned expenses/goals, or accepting a smaller terminal balance."
            ),
            iterations=0,
        )

    iterations = 0
    while hi - lo > TOLERANCE and iterations < MAX_ITERATIONS:
        mid = (lo + hi) / 2
        if objective(mid) >= ZERO:
            hi = mid
        else:
            lo = mid
        iterations += 1

    required = hi
    return SolverResult(
        target="required_corpus",
        feasible=True,
        value=required,
        value_today_rupees=required / _deflator(inp, delta),
        gap_vs_current=required - actual_corpus_at_retirement,
        message="Required corpus at retirement to fund the plan without a shortfall.",
        iterations=iterations,
    )


def solve_required_contribution(inp: ScenarioInput, desired_legacy: Decimal = ZERO) -> SolverResult:
    """FR-SOL-2: the smallest monthly SIP (respecting the configured step-up) that reaches the
    required corpus / sustains the plan without a shortfall.
    """
    upper_bound = (inp.annual_expense_today / 12) * 10
    if upper_bound <= ZERO:
        upper_bound = Decimal("1000000")

    def objective(sip: Decimal) -> Decimal:
        result = project(replace(inp, monthly_contribution=sip))
        if result.summary.exhaustion_age is None:
            return result.summary.terminal_corpus - desired_legacy
        return -result.summary.unfunded_shortfall_nominal

    lo, hi = ZERO, upper_bound
    if objective(hi) < ZERO:
        return SolverResult(
            target="required_contribution",
            feasible=False,
            value=None,
            value_today_rupees=None,
            gap_vs_current=None,
            message=(
                "No monthly contribution within a sane bound closes the gap. Consider retiring "
                "later, reducing planned expenses/goals, or accepting a smaller terminal balance."
            ),
            iterations=0,
        )

    iterations = 0
    while hi - lo > TOLERANCE and iterations < MAX_ITERATIONS:
        mid = (lo + hi) / 2
        if objective(mid) >= ZERO:
            hi = mid
        else:
            lo = mid
        iterations += 1

    required = hi
    return SolverResult(
        target="required_contribution",
        feasible=True,
        value=required,
        value_today_rupees=required,  # already a "today" monthly figure by construction
        gap_vs_current=required - inp.monthly_contribution,
        message="Required monthly contribution (SIP) to fund the plan without a shortfall.",
        iterations=iterations,
    )


def longevity_report(inp: ScenarioInput) -> SolverResult:
    """FR-SOL-3: not a bisection — just a readable summary of what the current plan already does."""
    result = project(inp)
    s = result.summary
    if s.exhaustion_age is None:
        message = f"Lasts beyond life expectancy, with a terminal surplus of \u20b9{s.terminal_corpus:,.0f}."
        value = Decimal(inp.life_expectancy)
    else:
        message = f"Corpus is exhausted at age {s.exhaustion_age}, {s.years_short} year(s) short of life expectancy."
        value = Decimal(s.exhaustion_age)
    return SolverResult(
        target="longevity",
        feasible=True,
        value=value,
        value_today_rupees=None,
        gap_vs_current=None,
        message=message,
        iterations=0,
    )
