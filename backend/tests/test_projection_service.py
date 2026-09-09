"""Unit tests for app/services/projection_service.py's override merging.

Regression coverage for a real bug found by driving the app end-to-end: `ProjectionOverrides.inputs`
is an untyped dict straight from the JSON body, so a money/rate field sent as a string (exactly how
the frontend sends every ScenarioInputs field on the wire) flowed unconverted into
`dataclasses.replace()` on the engine's Decimal-typed fields, and the engine's first
`Decimal + str` raised a 500 the instant any such field was overridden.
"""
from decimal import Decimal

from app.core.defaults import default_scenario_input
from app.core.engine import project
from app.schemas.projection import ProjectionOverrides
from app.services.projection_service import apply_overrides


def test_apply_overrides_coerces_decimal_fields_sent_as_strings():
    base = default_scenario_input()
    overrides = ProjectionOverrides(
        inputs={
            "retirement_age": 60,
            "monthly_contribution": "5000",
            "pre_retirement_return": "0.11",
            "expense_inflation": "0.06",
        }
    )

    merged = apply_overrides(base, overrides)

    assert merged.retirement_age == 60
    assert isinstance(merged.monthly_contribution, Decimal)
    assert merged.monthly_contribution == Decimal("5000")
    assert isinstance(merged.pre_retirement_return, Decimal)
    assert merged.pre_retirement_return == Decimal("0.11")
    assert isinstance(merged.expense_inflation, Decimal)

    # The real symptom: this used to raise TypeError deep inside the engine's arithmetic.
    result = project(merged)
    assert result.summary.verdict in ("sustainable", "shortfall")


def test_apply_overrides_accepts_already_decimal_values_unchanged():
    base = default_scenario_input()
    overrides = ProjectionOverrides(inputs={"monthly_contribution": Decimal("7500")})
    merged = apply_overrides(base, overrides)
    assert merged.monthly_contribution == Decimal("7500")


def test_apply_overrides_ignores_unknown_fields():
    base = default_scenario_input()
    overrides = ProjectionOverrides(inputs={"not_a_real_field": "123"})
    merged = apply_overrides(base, overrides)
    assert merged == base
