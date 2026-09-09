"""Scenario CRUD, duplication, projection and solving — FR-SCN-1..6, FR-ENG-*, FR-SOL-*.

Every route here is scoped to the authenticated user via `get_owned_scenario` (FR-AUTH-5): a
scenario id that exists but belongs to someone else returns 404, identically to one that does not
exist at all.
"""
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from app import models
from app.api.deps import get_current_user, get_db, get_owned_scenario
from app.core import engine as eng
from app.core import solver as slv
from app.core.defaults import default_scenario_input
from app.schemas.projection import ProjectionOut, ProjectionOverrides, SolveOut, SolveRequest
from app.schemas.scenario import (
    DependentIn,
    GoalIn,
    IncomeStreamIn,
    ScenarioCreate,
    ScenarioInputsIn,
    ScenarioListItem,
    ScenarioOut,
    ScenarioPatch,
    ScenarioReplace,
)
from app.services.projection_service import (
    apply_overrides,
    engine_result_to_schema,
    scenario_to_engine_input,
    solver_result_to_schema,
)

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


def _load(db: Session, scenario_id: int) -> models.Scenario | None:
    return (
        db.query(models.Scenario)
        .options(
            selectinload(models.Scenario.inputs),
            selectinload(models.Scenario.dependents),
            selectinload(models.Scenario.goals),
            selectinload(models.Scenario.income_streams),
        )
        .filter(models.Scenario.id == scenario_id)
        .first()
    )


def _orm_inputs_from_schema(inputs: ScenarioInputsIn) -> models.ScenarioInputs:
    return models.ScenarioInputs(
        current_age=inputs.current_age,
        retirement_age=inputs.retirement_age,
        life_expectancy=inputs.life_expectancy,
        plan_start_year=inputs.plan_start_year,
        current_corpus=inputs.current_corpus,
        monthly_contribution=inputs.monthly_contribution,
        contribution_stepup=inputs.contribution_stepup,
        contributions_stop_age=inputs.contributions_stop_age,
        pre_retirement_return=inputs.pre_retirement_return,
        post_retirement_return=inputs.post_retirement_return,
        annual_expense_today=inputs.annual_expense_today,
        expense_inflation=inputs.expense_inflation,
        charge_household_expense_pre_retirement=inputs.charge_household_expense_pre_retirement,
        medical_expense_today=inputs.medical_expense_today,
        medical_inflation=inputs.medical_inflation,
        post_retirement_expense_factor=inputs.post_retirement_expense_factor,
        engine_mode=inputs.engine_mode,
    )


def _orm_inputs_from_defaults(default: eng.ScenarioInput) -> models.ScenarioInputs:
    return models.ScenarioInputs(
        current_age=default.current_age,
        retirement_age=default.retirement_age,
        life_expectancy=default.life_expectancy,
        plan_start_year=default.plan_start_year,
        current_corpus=default.current_corpus,
        monthly_contribution=default.monthly_contribution,
        contribution_stepup=default.contribution_stepup,
        contributions_stop_age=default.contributions_stop_age,
        pre_retirement_return=default.pre_retirement_return,
        post_retirement_return=default.post_retirement_return,
        annual_expense_today=default.annual_expense_today,
        expense_inflation=default.expense_inflation,
        charge_household_expense_pre_retirement=default.charge_household_expense_pre_retirement,
        medical_expense_today=default.medical_expense_today,
        medical_inflation=default.medical_inflation,
        post_retirement_expense_factor=default.post_retirement_expense_factor,
        engine_mode=default.engine_mode,
    )


def _orm_dependent(d: DependentIn, sort_order: int) -> models.Dependent:
    return models.Dependent(sort_order=sort_order, **d.model_dump())


def _orm_dependent_from_engine(d: eng.Dependent, sort_order: int) -> models.Dependent:
    return models.Dependent(
        sort_order=sort_order,
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


def _orm_goal(g: GoalIn) -> models.Goal:
    return models.Goal(**g.model_dump())


def _orm_income(i: IncomeStreamIn) -> models.IncomeStream:
    return models.IncomeStream(**i.model_dump())


def _apply_scenario_inputs_patch(row: models.ScenarioInputs, updates: dict) -> None:
    for key, value in updates.items():
        if hasattr(row, key):
            setattr(row, key, value)


def _to_list_item(scenario: models.Scenario) -> ScenarioListItem:
    inp = scenario_to_engine_input(scenario)
    result = eng.project(inp)
    return ScenarioListItem(
        id=scenario.id,
        name=scenario.name,
        created_at=scenario.created_at,
        updated_at=scenario.updated_at,
        verdict=result.summary.verdict,
        exhaustion_age=result.summary.exhaustion_age,
        years_short=result.summary.years_short,
    )


@router.get("", response_model=list[ScenarioListItem])
def list_scenarios(
    db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
) -> list[ScenarioListItem]:
    scenarios = (
        db.query(models.Scenario)
        .options(
            selectinload(models.Scenario.inputs),
            selectinload(models.Scenario.dependents),
            selectinload(models.Scenario.goals),
            selectinload(models.Scenario.income_streams),
        )
        .filter(models.Scenario.user_id == current_user.id)
        .order_by(models.Scenario.updated_at.desc())
        .all()
    )
    return [_to_list_item(s) for s in scenarios]


@router.post("", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
def create_scenario(
    payload: ScenarioCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scenario:
    existing = (
        db.query(models.Scenario)
        .filter(models.Scenario.user_id == current_user.id, models.Scenario.name == payload.name)
        .first()
    )
    if existing is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="A scenario with this name already exists")

    scenario = models.Scenario(user_id=current_user.id, name=payload.name)

    # FR-SCN-5: each of inputs/dependents/goals/income_streams independently falls back to the
    # documented defaults (= the workbook's own sample data) when the caller omits it, so a bare
    # {"name": "..."} POST still produces a fully working, pre-filled scenario.
    default = default_scenario_input()

    scenario.inputs = (
        _orm_inputs_from_schema(payload.inputs) if payload.inputs is not None else _orm_inputs_from_defaults(default)
    )
    scenario.dependents = (
        [_orm_dependent(d, i) for i, d in enumerate(payload.dependents)]
        if payload.dependents is not None
        else [_orm_dependent_from_engine(d, i) for i, d in enumerate(default.dependents)]
    )
    scenario.goals = [_orm_goal(g) for g in payload.goals] if payload.goals is not None else []
    scenario.income_streams = (
        [_orm_income(i) for i in payload.income_streams] if payload.income_streams is not None else []
    )

    db.add(scenario)
    db.commit()
    return _load(db, scenario.id)


@router.get("/{scenario_id}", response_model=ScenarioOut)
def get_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scenario:
    get_owned_scenario(scenario_id, db, current_user)
    return _load(db, scenario_id)


@router.put("/{scenario_id}", response_model=ScenarioOut)
def replace_scenario(
    scenario_id: int,
    payload: ScenarioReplace,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scenario:
    scenario = get_owned_scenario(scenario_id, db, current_user)
    scenario.name = payload.name
    scenario.inputs = _orm_inputs_from_schema(payload.inputs)
    scenario.dependents = [_orm_dependent(d, i) for i, d in enumerate(payload.dependents)]
    scenario.goals = [_orm_goal(g) for g in payload.goals]
    scenario.income_streams = [_orm_income(i) for i in payload.income_streams]
    db.commit()
    return _load(db, scenario_id)


@router.patch("/{scenario_id}", response_model=ScenarioOut)
def patch_scenario(
    scenario_id: int,
    payload: ScenarioPatch,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scenario:
    scenario = get_owned_scenario(scenario_id, db, current_user)
    if payload.name is not None:
        scenario.name = payload.name
    if payload.inputs:
        _apply_scenario_inputs_patch(scenario.inputs, payload.inputs)
    if payload.dependents is not None:
        scenario.dependents = [_orm_dependent(d, i) for i, d in enumerate(payload.dependents)]
    if payload.goals is not None:
        scenario.goals = [_orm_goal(g) for g in payload.goals]
    if payload.income_streams is not None:
        scenario.income_streams = [_orm_income(i) for i in payload.income_streams]
    db.commit()

    # Re-validate the merged result against the same rules a full PUT would enforce (NFR-4).
    merged = _load(db, scenario_id)
    ScenarioInputsIn.model_validate(merged.inputs, from_attributes=True)
    return merged


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> None:
    scenario = get_owned_scenario(scenario_id, db, current_user)
    db.delete(scenario)
    db.commit()


@router.post("/{scenario_id}/duplicate", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
def duplicate_scenario(
    scenario_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> models.Scenario:
    original = get_owned_scenario(scenario_id, db, current_user)
    original = _load(db, scenario_id)

    base_name = f"{original.name} (copy)"
    name = base_name
    n = 2
    while db.query(models.Scenario).filter(
        models.Scenario.user_id == current_user.id, models.Scenario.name == name
    ).first():
        name = f"{base_name} {n}"
        n += 1

    copy = models.Scenario(user_id=current_user.id, name=name)
    src = original.inputs
    copy.inputs = models.ScenarioInputs(
        current_age=src.current_age,
        retirement_age=src.retirement_age,
        life_expectancy=src.life_expectancy,
        plan_start_year=src.plan_start_year,
        current_corpus=src.current_corpus,
        monthly_contribution=src.monthly_contribution,
        contribution_stepup=src.contribution_stepup,
        contributions_stop_age=src.contributions_stop_age,
        pre_retirement_return=src.pre_retirement_return,
        post_retirement_return=src.post_retirement_return,
        annual_expense_today=src.annual_expense_today,
        expense_inflation=src.expense_inflation,
        charge_household_expense_pre_retirement=src.charge_household_expense_pre_retirement,
        medical_expense_today=src.medical_expense_today,
        medical_inflation=src.medical_inflation,
        post_retirement_expense_factor=src.post_retirement_expense_factor,
        engine_mode=src.engine_mode,
    )
    copy.dependents = [
        models.Dependent(
            sort_order=d.sort_order,
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
        for d in original.dependents
    ]
    copy.goals = [
        models.Goal(
            label=g.label,
            amount_today=g.amount_today,
            at_age=g.at_age,
            inflation=g.inflation,
            recurrence=g.recurrence,
            recurrence_years=g.recurrence_years,
            duration_years=g.duration_years,
        )
        for g in original.goals
    ]
    copy.income_streams = [
        models.IncomeStream(
            label=i.label,
            monthly_amount_today=i.monthly_amount_today,
            start_age=i.start_age,
            end_age=i.end_age,
            annual_escalation=i.annual_escalation,
        )
        for i in original.income_streams
    ]
    db.add(copy)
    db.commit()
    return _load(db, copy.id)


@router.post("/{scenario_id}/project", response_model=ProjectionOut)
def project_scenario(
    scenario_id: int,
    overrides: ProjectionOverrides = ProjectionOverrides(),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> ProjectionOut:
    scenario = get_owned_scenario(scenario_id, db, current_user)
    scenario = _load(db, scenario_id)
    base = scenario_to_engine_input(scenario)
    inp = apply_overrides(base, overrides)
    result = eng.project(inp)
    return engine_result_to_schema(result, inp)


@router.post("/{scenario_id}/solve", response_model=SolveOut)
def solve_scenario(
    scenario_id: int,
    payload: SolveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
) -> SolveOut:
    scenario = get_owned_scenario(scenario_id, db, current_user)
    scenario = _load(db, scenario_id)
    inp = scenario_to_engine_input(scenario)

    if payload.target == "required_corpus":
        result = slv.solve_required_corpus(inp, desired_legacy=payload.desired_legacy)
    elif payload.target == "required_contribution":
        result = slv.solve_required_contribution(inp, desired_legacy=payload.desired_legacy)
    else:
        result = slv.longevity_report(inp)

    return solver_result_to_schema(result)
