"""Golden reconciliation against the source workbook (PRD.md §11, G1).

Reproduces the workbook's own defaults, including its literal (uncorrected) defect D6 behaviour
(`inflate_graduation_instalments=False`), in `annual_parity` mode, and asserts every pre-exhaustion
row matches the workbook's cached values within Rs 1. Rows from the exhaustion age (65) onward are
expected to diverge — the workbook's D1 bug lets a negative corpus keep earning a positive return
down to a fictitious -Rs17.34 crore by age 81 (PRD.md Appendix C); this engine floors the corpus at
zero instead (FR-ENG-5), which is the entire point of the project.
"""
from decimal import Decimal

import openpyxl
import pytest

from app.core.engine import Dependent, ScenarioInput, project
from tests.conftest import XLSX_PATH

TOLERANCE = Decimal("1")
WORKBOOK_EXHAUSTION_AGE = 65


def _workbook_literal_input() -> ScenarioInput:
    """The workbook's exact defaults, with the pre-correction defect D6 behaviour, so this
    reproduces the sheet's own arithmetic rather than the corrected recommended defaults in
    `core.defaults` (which intentionally differs — see that module's docstring).
    """
    common = dict(
        school_fee_hike=Decimal("0.25"),
        school_fee_hike_frequency=2,
        school_end_age=18,
        graduation_cost_today=Decimal("1200000"),
        graduation_inflation=Decimal("0.07"),
        graduation_start_age=18,
        graduation_duration=4,
        inflate_graduation_instalments=False,  # workbook's literal (frozen-instalment) behaviour
        marriage_cost_today=Decimal("500000"),
        marriage_inflation=Decimal("0.07"),
    )
    return ScenarioInput(
        current_age=43,
        retirement_age=43,
        life_expectancy=80,
        current_corpus=Decimal("15000000"),
        annual_expense_today=Decimal("600000"),
        expense_inflation=Decimal("0.07"),
        pre_retirement_return=Decimal("0.10"),
        post_retirement_return=Decimal("0.10"),
        charge_household_expense_pre_retirement=False,
        engine_mode="annual_parity",
        plan_start_year=2026,
        dependents=[
            Dependent(label="Son", current_age=13, school_fee_today=Decimal("200000"), marriage_age=28, **common),
            Dependent(label="Daughter", current_age=4, school_fee_today=Decimal("100000"), marriage_age=25, **common),
        ],
    )


@pytest.fixture(scope="module")
def workbook_rows():
    if not XLSX_PATH.exists():
        pytest.skip(f"source workbook not found at {XLSX_PATH}")
    wb = openpyxl.load_workbook(XLSX_PATH, data_only=True)
    ws = wb["Projection"]
    rows = {}
    for r in range(2, ws.max_row + 1):
        age = ws.cell(r, 2).value
        rows[age] = {
            "withdrawals": Decimal(str(ws.cell(r, 16).value)),
            "return": Decimal(str(ws.cell(r, 17).value)),
            "corpus_end": Decimal(str(ws.cell(r, 18).value)),
        }
    return rows


def test_pre_exhaustion_rows_match_workbook_within_one_rupee(workbook_rows):
    result = project(_workbook_literal_input())
    checked = 0
    for row in result.rows:
        if row.age >= WORKBOOK_EXHAUSTION_AGE:
            continue
        xl = workbook_rows[row.age]
        assert abs(row.outflow_total - xl["withdrawals"]) <= TOLERANCE, f"age {row.age} withdrawals"
        assert abs(row.investment_return - xl["return"]) <= TOLERANCE, f"age {row.age} return"
        assert abs(row.corpus_end - xl["corpus_end"]) <= TOLERANCE, f"age {row.age} corpus_end"
        checked += 1
    assert checked == WORKBOOK_EXHAUSTION_AGE - 43  # 22 rows, ages 43..64


def test_exhaustion_age_matches_workbook(workbook_rows):
    result = project(_workbook_literal_input())
    assert result.summary.exhaustion_age == WORKBOOK_EXHAUSTION_AGE


def test_corpus_never_goes_negative_unlike_the_workbook(workbook_rows):
    """The workbook's own age-81 row is -Rs14,97,90,010 (defect D1). This engine's row for the
    same age must be exactly zero, and every row must be non-negative.
    """
    result = project(_workbook_literal_input())
    for row in result.rows:
        assert row.corpus_end >= 0, f"age {row.age} corpus_end went negative: {row.corpus_end}"
        if row.age > WORKBOOK_EXHAUSTION_AGE:
            assert row.investment_return == 0, f"age {row.age} should earn no return once exhausted"


def test_projection_ends_at_life_expectancy_not_one_year_past():
    """Defect D2: the workbook's grid runs to age 81 against a life expectancy of 80."""
    result = project(_workbook_literal_input())
    ages = [row.age for row in result.rows]
    assert max(ages) == 80
    assert 81 not in ages
