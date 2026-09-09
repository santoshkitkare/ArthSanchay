"""The documented default input set (PRD.md §4.3), used to pre-fill every new scenario
(FR-SCN-5) and by the anonymous calculator. It mirrors the workbook's own sample data, but
with the *corrected* defaults where the PRD explicitly changed one (see PRD.md D6:
``inflate_graduation_instalments`` defaults to True here, unlike the workbook's frozen
instalments). The workbook's literal, uncorrected behaviour is reproduced separately in
``tests/test_engine_parity.py`` for the golden reconciliation.
"""
from decimal import Decimal

from app.core.engine import Dependent, ScenarioInput


def default_scenario_input() -> ScenarioInput:
    return ScenarioInput(
        current_age=43,
        retirement_age=43,
        life_expectancy=80,
        current_corpus=Decimal("15000000"),
        annual_expense_today=Decimal("600000"),
        expense_inflation=Decimal("0.07"),
        pre_retirement_return=Decimal("0.10"),
        post_retirement_return=Decimal("0.10"),
        monthly_contribution=Decimal("0"),
        contribution_stepup=Decimal("0"),
        contributions_stop_age=None,  # resolves to retirement_age
        medical_expense_today=Decimal("0"),
        medical_inflation=Decimal("0.10"),
        charge_household_expense_pre_retirement=False,
        post_retirement_expense_factor=Decimal("1.0"),
        engine_mode="monthly",
        plan_start_year=2026,
        dependents=[
            Dependent(
                label="Child 1",
                current_age=13,
                school_fee_today=Decimal("200000"),
                school_fee_hike=Decimal("0.25"),
                school_fee_hike_frequency=2,
                school_end_age=18,
                graduation_cost_today=Decimal("1200000"),
                graduation_inflation=Decimal("0.07"),
                graduation_start_age=18,
                graduation_duration=4,
                inflate_graduation_instalments=True,
                marriage_cost_today=Decimal("500000"),
                marriage_inflation=Decimal("0.07"),
                marriage_age=28,
                fund_school_from_corpus_pre_retirement=True,
            ),
            Dependent(
                label="Child 2",
                current_age=4,
                school_fee_today=Decimal("100000"),
                school_fee_hike=Decimal("0.25"),
                school_fee_hike_frequency=2,
                school_end_age=18,
                graduation_cost_today=Decimal("1200000"),
                graduation_inflation=Decimal("0.07"),
                graduation_start_age=18,
                graduation_duration=4,
                inflate_graduation_instalments=True,
                marriage_cost_today=Decimal("500000"),
                marriage_inflation=Decimal("0.07"),
                marriage_age=25,
                fund_school_from_corpus_pre_retirement=True,
            ),
        ],
        goals=[],
        income_streams=[],
    )
