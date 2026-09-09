"""Solver tests — convergence and round-trip consistency (PRD.md §5.8, §5.9, §11)."""
from dataclasses import replace
from decimal import Decimal

from app.core.defaults import default_scenario_input
from app.core.engine import Dependent, project
from app.core.solver import longevity_report, solve_required_contribution, solve_required_corpus

D = Decimal


def test_required_corpus_round_trips_to_a_sustainable_plan():
    inp = default_scenario_input()  # retirement_age == current_age in the sample data
    baseline = project(inp)
    assert baseline.summary.verdict == "shortfall"  # sanity: this scenario does need solving

    result = solve_required_corpus(inp)
    assert result.feasible
    assert result.value > inp.current_corpus  # more corpus is needed, not less

    delta = inp.retirement_age - inp.current_age
    shifted = replace(
        inp,
        current_age=inp.retirement_age,
        dependents=[replace(d, current_age=d.current_age + delta) for d in inp.dependents],
        current_corpus=result.value,
    )
    check = project(shifted)
    assert check.summary.verdict == "sustainable"
    assert check.summary.exhaustion_age is None


def test_required_corpus_is_close_to_minimal():
    """A corpus meaningfully below the solved value should fail; this guards against a solver
    that overshoots by a wide margin.
    """
    inp = default_scenario_input()
    result = solve_required_corpus(inp)
    delta = inp.retirement_age - inp.current_age
    shifted = replace(
        inp,
        current_age=inp.retirement_age,
        dependents=[replace(d, current_age=d.current_age + delta) for d in inp.dependents],
        current_corpus=result.value * D("0.99"),
    )
    check = project(shifted)
    assert check.summary.verdict == "shortfall"


def test_required_contribution_round_trips_when_feasible():
    inp = replace(default_scenario_input(), retirement_age=60)  # gives a real accumulation window
    result = solve_required_contribution(inp)
    assert result.feasible

    check = project(replace(inp, monthly_contribution=result.value))
    assert check.summary.verdict == "sustainable"


def test_required_contribution_reports_infeasible_when_no_accumulation_window_exists():
    """When retirement_age == current_age there is no pre-retirement period during which a
    monthly SIP can ever apply, so no contribution — however large — can help. The solver must
    say so structurally (FR-SOL-5), not return a misleadingly large number.
    """
    inp = default_scenario_input()  # retirement_age == current_age
    result = solve_required_contribution(inp)
    assert result.feasible is False
    assert result.value is None
    assert "retiring later" in result.message or "expenses" in result.message


def test_longevity_report_matches_the_engines_own_summary():
    inp = default_scenario_input()
    projection = project(inp)
    report = longevity_report(inp)
    assert report.feasible is True
    if projection.summary.exhaustion_age is not None:
        assert int(report.value) == projection.summary.exhaustion_age
    else:
        assert int(report.value) == inp.life_expectancy


def test_higher_starting_corpus_never_produces_a_worse_outcome():
    """Monotonicity property the bisection depends on (PRD.md §11)."""
    inp = replace(default_scenario_input(), retirement_age=55)
    low = project(replace(inp, current_corpus=D("10000000")))
    high = project(replace(inp, current_corpus=D("30000000")))
    assert high.summary.terminal_corpus >= low.summary.terminal_corpus
    if low.summary.exhaustion_age is not None and high.summary.exhaustion_age is not None:
        assert high.summary.exhaustion_age >= low.summary.exhaustion_age
