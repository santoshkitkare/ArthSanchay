"""Glue between the ORM/Pydantic layers and the pure `core.engine`/`core.solver` modules.
Nothing here performs I/O beyond what its caller already did; it only converts data shapes.
"""
from dataclasses import replace
from decimal import Decimal

from app import models
from app.core import engine as eng
from app.schemas.projection import (
    ProjectionMeta,
    ProjectionOut,
    ProjectionOverrides,
    RowOut,
    SolveOut,
    SummaryOut,
)
from app.schemas.scenario import (
    DependentIn,
    GoalIn,
    IncomeStreamIn,
    ScenarioInputsIn,
)


def _dependent_in_to_engine(d: DependentIn) -> eng.Dependent:
    return eng.Dependent(
        label=d.label,
        current_age=d.current_age,
        school_fee_today=d.school_fee_today,
        school_fee_hike=d.school_fee_hike,
        school_fee_hike_frequency=d.school_fee_hike_frequency,
        school_end_age=d.school_end_age,
        graduation_cost_today=d.graduation_cost_today,
        graduation_inflation=d.graduation_inflation,
        graduation_start_age=d.graduation_start_age,
        graduation_duration=d.graduation_duration,
        inflate_graduation_instalments=d.inflate_graduation_instalments,
        marriage_cost_today=d.marriage_cost_today,
        marriage_inflation=d.marriage_inflation,
        marriage_age=d.marriage_age,
        fund_school_from_corpus_pre_retirement=d.fund_school_from_corpus_pre_retirement,
    )


def _dependent_orm_to_engine(d: models.Dependent) -> eng.Dependent:
    return eng.Dependent(
        label=d.label,
        current_age=d.current_age,
        school_fee_today=Decimal(d.school_fee_today),
        school_fee_hike=Decimal(d.school_fee_hike),
        school_fee_hike_frequency=d.school_fee_hike_frequency,
        school_end_age=d.school_end_age,
        graduation_cost_today=Decimal(d.graduation_cost_today),
        graduation_inflation=Decimal(d.graduation_inflation),
        graduation_start_age=d.graduation_start_age,
        graduation_duration=d.graduation_duration,
        inflate_graduation_instalments=d.inflate_graduation_instalments,
        marriage_cost_today=Decimal(d.marriage_cost_today),
        marriage_inflation=Decimal(d.marriage_inflation),
        marriage_age=d.marriage_age,
        fund_school_from_corpus_pre_retirement=d.fund_school_from_corpus_pre_retirement,
    )


def _goal_in_to_engine(g: GoalIn) -> eng.Goal:
    return eng.Goal(
        label=g.label,
        amount_today=g.amount_today,
        at_age=g.at_age,
        inflation=g.inflation,
        recurrence=g.recurrence,
        recurrence_years=g.recurrence_years,
        duration_years=g.duration_years,
    )


def _goal_orm_to_engine(g: models.Goal) -> eng.Goal:
    return eng.Goal(
        label=g.label,
        amount_today=Decimal(g.amount_today),
        at_age=g.at_age,
        inflation=Decimal(g.inflation),
        recurrence=g.recurrence,
        recurrence_years=g.recurrence_years,
        duration_years=g.duration_years,
    )


def _income_in_to_engine(i: IncomeStreamIn) -> eng.IncomeStream:
    return eng.IncomeStream(
        label=i.label,
        monthly_amount_today=i.monthly_amount_today,
        start_age=i.start_age,
        end_age=i.end_age,
        annual_escalation=i.annual_escalation,
    )


def _income_orm_to_engine(i: models.IncomeStream) -> eng.IncomeStream:
    return eng.IncomeStream(
        label=i.label,
        monthly_amount_today=Decimal(i.monthly_amount_today),
        start_age=i.start_age,
        end_age=i.end_age,
        annual_escalation=Decimal(i.annual_escalation),
    )


def inputs_in_to_engine(
    inputs: ScenarioInputsIn,
    dependents: list[DependentIn],
    goals: list[GoalIn],
    income_streams: list[IncomeStreamIn],
) -> eng.ScenarioInput:
    return eng.ScenarioInput(
        current_age=inputs.current_age,
        retirement_age=inputs.retirement_age,
        life_expectancy=inputs.life_expectancy,
        current_corpus=inputs.current_corpus,
        annual_expense_today=inputs.annual_expense_today,
        expense_inflation=inputs.expense_inflation,
        pre_retirement_return=inputs.pre_retirement_return,
        post_retirement_return=inputs.post_retirement_return,
        monthly_contribution=inputs.monthly_contribution,
        contribution_stepup=inputs.contribution_stepup,
        contributions_stop_age=inputs.contributions_stop_age,
        medical_expense_today=inputs.medical_expense_today,
        medical_inflation=inputs.medical_inflation,
        charge_household_expense_pre_retirement=inputs.charge_household_expense_pre_retirement,
        post_retirement_expense_factor=inputs.post_retirement_expense_factor,
        engine_mode=inputs.engine_mode,
        plan_start_year=inputs.plan_start_year,
        dependents=[_dependent_in_to_engine(d) for d in dependents],
        goals=[_goal_in_to_engine(g) for g in goals],
        income_streams=[_income_in_to_engine(i) for i in income_streams],
    )


def scenario_to_engine_input(scenario: models.Scenario) -> eng.ScenarioInput:
    si = scenario.inputs
    return eng.ScenarioInput(
        current_age=si.current_age,
        retirement_age=si.retirement_age,
        life_expectancy=si.life_expectancy,
        current_corpus=Decimal(si.current_corpus),
        annual_expense_today=Decimal(si.annual_expense_today),
        expense_inflation=Decimal(si.expense_inflation),
        pre_retirement_return=Decimal(si.pre_retirement_return),
        post_retirement_return=Decimal(si.post_retirement_return),
        monthly_contribution=Decimal(si.monthly_contribution),
        contribution_stepup=Decimal(si.contribution_stepup),
        contributions_stop_age=si.contributions_stop_age,
        medical_expense_today=Decimal(si.medical_expense_today),
        medical_inflation=Decimal(si.medical_inflation),
        charge_household_expense_pre_retirement=si.charge_household_expense_pre_retirement,
        post_retirement_expense_factor=Decimal(si.post_retirement_expense_factor),
        engine_mode=si.engine_mode,
        plan_start_year=si.plan_start_year,
        dependents=[_dependent_orm_to_engine(d) for d in scenario.dependents],
        goals=[_goal_orm_to_engine(g) for g in scenario.goals],
        income_streams=[_income_orm_to_engine(i) for i in scenario.income_streams],
    )


def apply_overrides(base: eng.ScenarioInput, overrides: ProjectionOverrides) -> eng.ScenarioInput:
    """Merge a transient what-if body (§8.3's slider strip) onto a base engine input. Only
    scalar fields present in `overrides.inputs` are changed; dependents/goals/income_streams are
    replaced wholesale when provided, otherwise left as-is.
    """
    scalar_updates = {k: v for k, v in overrides.inputs.items() if hasattr(base, k)}
    merged = replace(base, **scalar_updates) if scalar_updates else base
    if overrides.dependents is not None:
        merged = replace(merged, dependents=[_dependent_in_to_engine(d) for d in overrides.dependents])
    if overrides.goals is not None:
        merged = replace(merged, goals=[_goal_in_to_engine(g) for g in overrides.goals])
    if overrides.income_streams is not None:
        merged = replace(merged, income_streams=[_income_in_to_engine(i) for i in overrides.income_streams])
    return merged


def engine_result_to_schema(result: eng.ProjectionResult, inp: eng.ScenarioInput) -> ProjectionOut:
    s = result.summary
    return ProjectionOut(
        mode=result.mode,
        meta=ProjectionMeta(
            plan_start_year=inp.plan_start_year,
            months=len(result.rows) if result.mode == "monthly" else len(result.rows) * 12,
            current_age=inp.current_age,
            retirement_age=inp.retirement_age,
            life_expectancy=inp.life_expectancy,
        ),
        summary=SummaryOut(
            verdict=s.verdict,
            corpus_at_retirement=s.corpus_at_retirement,
            peak_corpus=s.peak_corpus,
            peak_age=s.peak_age,
            exhaustion_age=s.exhaustion_age,
            years_short=s.years_short,
            terminal_corpus=s.terminal_corpus,
            unfunded_shortfall_nominal=s.unfunded_shortfall_nominal,
            unfunded_shortfall_today=s.unfunded_shortfall_today,
            total_withdrawals=s.total_withdrawals,
            total_contributions=s.total_contributions,
            total_return=s.total_return,
            first_year_withdrawal_rate=s.first_year_withdrawal_rate,
        ),
        rows=[
            RowOut(
                t=r.t,
                year=r.year,
                age=r.age,
                month=r.month,
                corpus_start=r.corpus_start,
                inflow_contribution=r.inflow_contribution,
                inflow_income=r.inflow_income,
                household=r.household,
                medical=r.medical,
                school=r.school,
                graduation=r.graduation,
                marriage=r.marriage,
                custom=r.custom,
                outflow_total=r.outflow_total,
                investment_return=r.investment_return,
                corpus_end=r.corpus_end,
                corpus_end_today_rupees=r.corpus_end_today_rupees,
                shortfall=r.shortfall,
                events=r.events,
            )
            for r in result.rows
        ],
    )


def solver_result_to_schema(result) -> SolveOut:  # result: core.solver.SolverResult
    return SolveOut(
        target=result.target,
        feasible=result.feasible,
        value=result.value,
        value_today_rupees=result.value_today_rupees,
        gap_vs_current=result.gap_vs_current,
        message=result.message,
        iterations=result.iterations,
    )
