// Mirrors backend/app/schemas/*.py. Decimal fields arrive as JSON strings (pydantic v2's default
// Decimal serialization), so money/rate fields are typed `string` here and parsed for display or
// editing via src/lib/money.ts — never coerced through `number` internally, to avoid float drift.

export type EngineMode = "monthly" | "annual_parity";
export type GoalRecurrence = "once" | "annual" | "every_n_years";
export type Verdict = "sustainable" | "shortfall";
export type SolverTarget = "required_corpus" | "required_contribution" | "longevity";

export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface ScenarioInputs {
  current_age: number;
  retirement_age: number;
  life_expectancy: number;
  plan_start_year: number;
  current_corpus: string;
  monthly_contribution: string;
  contribution_stepup: string;
  contributions_stop_age: number | null;
  pre_retirement_return: string;
  post_retirement_return: string;
  annual_expense_today: string;
  expense_inflation: string;
  charge_household_expense_pre_retirement: boolean;
  medical_expense_today: string;
  medical_inflation: string;
  post_retirement_expense_factor: string;
  engine_mode: EngineMode;
}

export interface Dependent {
  id?: number;
  label: string;
  current_age: number;
  school_fee_today: string;
  school_fee_hike: string;
  school_fee_hike_frequency: number;
  school_end_age: number;
  graduation_cost_today: string;
  graduation_inflation: string;
  graduation_start_age: number;
  graduation_duration: number;
  inflate_graduation_instalments: boolean;
  marriage_cost_today: string;
  marriage_inflation: string;
  marriage_age: number | null;
  fund_school_from_corpus_pre_retirement: boolean;
}

export interface Goal {
  id?: number;
  label: string;
  amount_today: string;
  at_age: number;
  inflation: string;
  recurrence: GoalRecurrence;
  recurrence_years: number | null;
  duration_years: number | null;
}

export interface IncomeStream {
  id?: number;
  label: string;
  monthly_amount_today: string;
  start_age: number;
  end_age: number | null;
  annual_escalation: string;
}

export interface Scenario {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  inputs: ScenarioInputs;
  dependents: Dependent[];
  goals: Goal[];
  income_streams: IncomeStream[];
}

export interface ScenarioListItem {
  id: number;
  name: string;
  created_at: string;
  updated_at: string;
  verdict: Verdict;
  exhaustion_age: number | null;
  years_short: number;
}

export interface ProjectionRow {
  t: number;
  year: number;
  age: number;
  month: number;
  corpus_start: string;
  inflow_contribution: string;
  inflow_income: string;
  household: string;
  medical: string;
  school: string;
  graduation: string;
  marriage: string;
  custom: string;
  outflow_total: string;
  investment_return: string;
  corpus_end: string;
  corpus_end_today_rupees: string;
  shortfall: string;
  events: string[];
}

export interface ProjectionSummary {
  verdict: Verdict;
  corpus_at_retirement: string;
  peak_corpus: string;
  peak_age: number;
  exhaustion_age: number | null;
  years_short: number;
  terminal_corpus: string;
  unfunded_shortfall_nominal: string;
  unfunded_shortfall_today: string;
  total_withdrawals: string;
  total_contributions: string;
  total_return: string;
  first_year_withdrawal_rate: string;
}

export interface ProjectionMeta {
  plan_start_year: number;
  months: number;
  current_age: number;
  retirement_age: number;
  life_expectancy: number;
}

export interface ProjectionResult {
  mode: EngineMode;
  meta: ProjectionMeta;
  summary: ProjectionSummary;
  rows: ProjectionRow[];
}

export interface SolveResult {
  target: SolverTarget;
  feasible: boolean;
  value: string | null;
  value_today_rupees: string | null;
  gap_vs_current: string | null;
  message: string;
  iterations: number;
}

export interface ProjectionOverrides {
  inputs?: Partial<ScenarioInputs>;
  dependents?: Dependent[];
  goals?: Goal[];
  income_streams?: IncomeStream[];
}

// Flat shape driving the scenario edit form (src/components/forms/ScenarioForm.tsx).
export interface ScenarioFormValues {
  name: string;
  inputs: ScenarioInputs;
  dependents: Dependent[];
  goals: Goal[];
  income_streams: IncomeStream[];
}
