"""Unit tests for the individual formulas and the monthly-mode engine (PRD.md §5.2, §5.3, §5.5)."""
from decimal import Decimal

from app.core.engine import (
    Dependent,
    Goal,
    IncomeStream,
    ScenarioInput,
    _goal_years,
    goal_amount_for_year,
    graduation_cost,
    household_expense,
    income_amount,
    marriage_cost,
    monthly_rate,
    project,
    school_fee,
    sip_amount,
)

D = Decimal


def minimal_input(**overrides) -> ScenarioInput:
    base = dict(
        current_age=40,
        retirement_age=45,
        life_expectancy=50,
        current_corpus=D("1000000"),
        annual_expense_today=D("120000"),
        expense_inflation=D("0.05"),
        pre_retirement_return=D("0.08"),
        post_retirement_return=D("0.06"),
    )
    base.update(overrides)
    return ScenarioInput(**base)


# --------------------------------------------------------------------------------------
# Rate conversion (FR-ENG-3)
# --------------------------------------------------------------------------------------


def test_monthly_rate_compounds_to_exact_annual_rate():
    for annual in (D("0.10"), D("0.07"), D("0"), D("-0.05"), D("0.35")):
        rm = monthly_rate(annual)
        compounded = (D(1) + rm) ** 12 - D(1)
        assert abs(compounded - annual) < D("1e-20")


def test_monthly_rate_is_not_simple_division():
    """10% / 12 = 0.008333..., but the geometric rate must differ from that (FR-ENG-3)."""
    rm = monthly_rate(D("0.10"))
    assert rm != D("0.10") / 12


# --------------------------------------------------------------------------------------
# Household expense
# --------------------------------------------------------------------------------------


def test_household_expense_zero_before_retirement_by_default():
    inp = minimal_input()
    assert household_expense(inp, y=0) == 0  # age 40, retirement 45


def test_household_expense_nonzero_from_retirement_and_inflates():
    inp = minimal_input()
    y_at_retirement = inp.retirement_age - inp.current_age
    expected_at_retirement = inp.annual_expense_today * D("1.05") ** y_at_retirement
    assert household_expense(inp, y_at_retirement) == expected_at_retirement
    assert household_expense(inp, y_at_retirement + 1) == inp.annual_expense_today * D("1.05") ** (y_at_retirement + 1)


def test_household_expense_charged_pre_retirement_when_toggled_on():
    inp = minimal_input(charge_household_expense_pre_retirement=True)
    assert household_expense(inp, y=0) == inp.annual_expense_today


def test_post_retirement_expense_factor_applies_only_after_retirement():
    inp = minimal_input(post_retirement_expense_factor=D("0.8"), charge_household_expense_pre_retirement=True)
    y_before = 0
    y_at_ret = inp.retirement_age - inp.current_age
    assert household_expense(inp, y_before) == inp.annual_expense_today  # y=0: no inflation yet, no factor yet
    assert household_expense(inp, y_at_ret) == inp.annual_expense_today * D("1.05") ** y_at_ret * D("0.8")


# --------------------------------------------------------------------------------------
# School fee
# --------------------------------------------------------------------------------------


def test_school_fee_steps_every_frequency_years_and_stops_at_end_age():
    dep = Dependent(label="X", current_age=16, school_fee_today=D("100000"), school_fee_hike=D("0.25"),
                     school_fee_hike_frequency=2, school_end_age=18)
    assert school_fee(dep, current_age=40, y=0) == D("100000")  # age 16, step 0
    assert school_fee(dep, current_age=40, y=1) == D("100000")  # age 17, still step 0 (1//2=0)
    assert school_fee(dep, current_age=40, y=2) == 0  # age 18 == school_end_age -> stops


def test_school_fee_zero_once_dependent_reaches_end_age():
    dep = Dependent(label="X", current_age=17, school_fee_today=D("50000"), school_end_age=18)
    assert school_fee(dep, current_age=40, y=0) == D("50000")  # age 17
    assert school_fee(dep, current_age=40, y=1) == 0  # age 18


def test_school_end_age_is_configurable_unlike_the_workbook():
    """Defect D7: the workbook hardcoded 18. Here it's a per-dependent field."""
    dep = Dependent(label="X", current_age=17, school_fee_today=D("50000"), school_end_age=21)
    assert school_fee(dep, current_age=40, y=1) == D("50000")  # age 18, still schooling


# --------------------------------------------------------------------------------------
# Graduation
# --------------------------------------------------------------------------------------


def test_graduation_fires_only_within_its_window_and_splits_evenly():
    dep = Dependent(label="X", current_age=16, graduation_cost_today=D("400000"), graduation_inflation=D("0"),
                     graduation_start_age=18, graduation_duration=4, inflate_graduation_instalments=False)
    assert graduation_cost(dep, y=0) == 0  # age 16
    assert graduation_cost(dep, y=1) == 0  # age 17
    for y in (2, 3, 4, 5):  # ages 18-21
        assert graduation_cost(dep, y) == D("100000")
    assert graduation_cost(dep, y=6) == 0  # age 22


def test_graduation_frozen_vs_inflated_instalments_defect_d6():
    dep_frozen = Dependent(label="X", current_age=16, graduation_cost_today=D("400000"),
                            graduation_inflation=D("0.10"), graduation_start_age=18, graduation_duration=4,
                            inflate_graduation_instalments=False)
    dep_inflated = Dependent(label="X", current_age=16, graduation_cost_today=D("400000"),
                              graduation_inflation=D("0.10"), graduation_start_age=18, graduation_duration=4,
                              inflate_graduation_instalments=True)
    # Both start identically at age 18 (y=2, exponent 2 in both formulas).
    assert graduation_cost(dep_frozen, y=2) == graduation_cost(dep_inflated, y=2)
    # But the age-21 instalment (y=5) differs: frozen keeps the age-18 price, inflated does not.
    assert graduation_cost(dep_frozen, y=5) == graduation_cost(dep_frozen, y=2)
    assert graduation_cost(dep_inflated, y=5) > graduation_cost(dep_inflated, y=2)


# --------------------------------------------------------------------------------------
# Marriage
# --------------------------------------------------------------------------------------


def test_marriage_fires_exactly_once_at_marriage_age():
    dep = Dependent(label="X", current_age=20, marriage_cost_today=D("500000"), marriage_inflation=D("0.07"),
                     marriage_age=28)
    for y in range(0, 8):  # ages 20-27: not yet married
        assert marriage_cost(dep, y) == 0
    assert marriage_cost(dep, y=8) == D("500000") * D("1.07") ** 8  # age 28
    assert marriage_cost(dep, y=9) == 0  # age 29: already fired, no repeat


def test_marriage_none_when_marriage_age_is_none():
    dep = Dependent(label="X", current_age=20, marriage_cost_today=D("500000"), marriage_age=None)
    for y in range(0, 20):
        assert marriage_cost(dep, y) == 0


# --------------------------------------------------------------------------------------
# Custom goals
# --------------------------------------------------------------------------------------


def test_goal_once_fires_a_single_year():
    goal = Goal(label="Car", amount_today=D("1000000"), at_age=50, recurrence="once")
    years = _goal_years(goal, current_age=40, life_expectancy=80)
    assert years == [10]


def test_goal_annual_recurs_for_duration():
    goal = Goal(label="Travel", amount_today=D("200000"), at_age=50, recurrence="annual", duration_years=3)
    years = _goal_years(goal, current_age=40, life_expectancy=80)
    assert years == [10, 11, 12]


def test_goal_annual_open_ended_runs_to_life_expectancy():
    goal = Goal(label="Pension top-up", amount_today=D("50000"), at_age=78, recurrence="annual", duration_years=None)
    years = _goal_years(goal, current_age=40, life_expectancy=80)
    assert years == [38, 39, 40]  # ages 78, 79, 80


def test_goal_every_n_years_steps_correctly():
    goal = Goal(label="Car replacement", amount_today=D("800000"), at_age=45, recurrence="every_n_years",
                recurrence_years=5, duration_years=16)
    years = _goal_years(goal, current_age=40, life_expectancy=80)
    assert years == [5, 10, 15, 20]


def test_goal_amount_inflates_from_today():
    goal = Goal(label="X", amount_today=D("100000"), at_age=45, inflation=D("0.10"))
    assert goal_amount_for_year(goal, y=0) == D("100000")
    assert goal_amount_for_year(goal, y=5) == D("100000") * D("1.10") ** 5


# --------------------------------------------------------------------------------------
# Contributions and income
# --------------------------------------------------------------------------------------


def test_sip_stops_at_configured_age():
    inp = minimal_input(monthly_contribution=D("10000"), contributions_stop_age=45)
    assert sip_amount(inp, y=4) == D("10000") * D("1") ** 4  # age 44, still contributing
    assert sip_amount(inp, y=5) == 0  # age 45, stopped


def test_sip_defaults_to_stopping_at_retirement_age():
    inp = minimal_input(monthly_contribution=D("10000"))  # retirement_age=45, contributions_stop_age=None
    assert inp.resolved_contributions_stop_age == 45
    assert sip_amount(inp, y=4) > 0
    assert sip_amount(inp, y=5) == 0


def test_sip_step_up_compounds_annually():
    inp = minimal_input(monthly_contribution=D("10000"), contribution_stepup=D("0.10"), contributions_stop_age=100)
    assert sip_amount(inp, y=0) == D("10000")
    assert sip_amount(inp, y=1) == D("10000") * D("1.10")


def test_income_stream_respects_start_and_end_age():
    stream = IncomeStream(label="Pension", monthly_amount_today=D("30000"), start_age=60, end_age=70)
    assert income_amount(stream, current_age=40, y=19) == 0  # age 59
    assert income_amount(stream, current_age=40, y=20) == D("30000")  # age 60
    assert income_amount(stream, current_age=40, y=30) == D("30000")  # age 70, still on
    assert income_amount(stream, current_age=40, y=31) == 0  # age 71, ended


def test_income_stream_open_ended_when_no_end_age():
    stream = IncomeStream(label="Rent", monthly_amount_today=D("15000"), start_age=50, end_age=None)
    assert income_amount(stream, current_age=40, y=50) == D("15000")  # age 90, still on


# --------------------------------------------------------------------------------------
# Floor / exhaustion behaviour in monthly mode (FR-ENG-5, FR-ENG-6, FR-ENG-7)
# --------------------------------------------------------------------------------------


def test_monthly_mode_floors_corpus_at_zero_and_stops_earning_return():
    """A tiny corpus against large expenses must hit exactly zero and never go negative or
    earn a return once exhausted (the fix for defect D1).
    """
    inp = minimal_input(
        current_corpus=D("10000"),
        retirement_age=40,  # retired immediately
        annual_expense_today=D("500000"),
        engine_mode="monthly",
    )
    result = project(inp)
    assert result.summary.exhaustion_age is not None
    negative_rows = [r for r in result.rows if r.corpus_end < 0]
    assert negative_rows == []
    post_exhaustion_returns = [r.investment_return for r in result.rows if r.shortfall > 0]
    assert all(r == 0 for r in post_exhaustion_returns)
    assert result.summary.unfunded_shortfall_nominal > 0


def test_projection_never_runs_past_life_expectancy():
    inp = minimal_input(life_expectancy=42, engine_mode="monthly")
    result = project(inp)
    assert max(r.age for r in result.rows) == 42
    assert len(result.rows) == (42 - 40 + 1) * 12


def test_sustainable_plan_has_no_exhaustion_and_positive_terminal_corpus():
    inp = minimal_input(current_corpus=D("50000000"), annual_expense_today=D("100000"), engine_mode="monthly")
    result = project(inp)
    assert result.summary.verdict == "sustainable"
    assert result.summary.exhaustion_age is None
    assert result.summary.terminal_corpus > 0
