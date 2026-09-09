import { useForm } from "react-hook-form";
import { Link } from "react-router-dom";
import { useState } from "react";
import { MoneyField } from "../components/forms/MoneyField";
import { PercentField } from "../components/forms/PercentField";
import { VerdictBanner } from "../components/dashboard/VerdictBanner";
import { MetricTiles } from "../components/dashboard/MetricTiles";
import { CorpusTimelineChart } from "../components/charts/CorpusTimelineChart";
import { projectAnonymous } from "../api/scenarios";
import type { ProjectionResult, ScenarioInputs } from "../types";
import { ApiError } from "../api/client";

const DEFAULTS: ScenarioInputs = {
  current_age: 30,
  retirement_age: 55,
  life_expectancy: 85,
  plan_start_year: new Date().getFullYear(),
  current_corpus: "2000000",
  monthly_contribution: "25000",
  contribution_stepup: "0.05",
  contributions_stop_age: null,
  pre_retirement_return: "0.12",
  post_retirement_return: "0.08",
  annual_expense_today: "600000",
  expense_inflation: "0.06",
  charge_household_expense_pre_retirement: false,
  medical_expense_today: "50000",
  medical_inflation: "0.10",
  post_retirement_expense_factor: "1.0",
  engine_mode: "monthly",
};

/** The anonymous, no-login calculator (PRD.md §8.1) — a trimmed version of the full input model,
 * just enough to demonstrate the projection and chart before asking for a signup.
 */
export function LandingPage() {
  const { control, register, handleSubmit } = useForm<ScenarioInputs>({ defaultValues: DEFAULTS });
  const [result, setResult] = useState<ProjectionResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (inputs: ScenarioInputs) => {
    setLoading(true);
    setError(null);
    try {
      const r = await projectAnonymous(inputs);
      setResult(r);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not calculate a projection");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="page landing-page">
      <header className="page-header">
        <h1>ArthSanchay</h1>
        <div>
          <Link to="/login">Log in</Link> · <Link to="/register">Sign up</Link>
        </div>
      </header>

      <p className="lede">
        See how your investments, expenses, and inflation play out from today to your life expectancy — no
        account required for a quick look. Sign up to save scenarios, add dependents and goals, and get the
        corpus you need at retirement.
      </p>

      <form onSubmit={handleSubmit(onSubmit)} className="landing-form">
        <label className="field">
          <span className="field-label">Current age</span>
          <input type="number" {...register("current_age", { valueAsNumber: true })} />
        </label>
        <label className="field">
          <span className="field-label">Retirement age</span>
          <input type="number" {...register("retirement_age", { valueAsNumber: true })} />
        </label>
        <label className="field">
          <span className="field-label">Life expectancy</span>
          <input type="number" {...register("life_expectancy", { valueAsNumber: true })} />
        </label>
        <MoneyField control={control} name="current_corpus" label="Current investments" />
        <MoneyField control={control} name="monthly_contribution" label="Monthly SIP" />
        <MoneyField control={control} name="annual_expense_today" label="Annual expenses today" />
        <PercentField control={control} name="expense_inflation" label="Expense inflation" />
        <PercentField control={control} name="pre_retirement_return" label="Pre-retirement return" />
        <PercentField control={control} name="post_retirement_return" label="Post-retirement return" />
        <button type="submit" disabled={loading}>
          {loading ? "Calculating…" : "Calculate"}
        </button>
      </form>

      {error && <div className="form-error">{error}</div>}

      {result && (
        <div className="landing-results">
          <VerdictBanner result={result} />
          <MetricTiles result={result} />
          <CorpusTimelineChart result={result} />
        </div>
      )}

      <footer className="disclaimer">
        This is an illustrative projection based on your own assumptions, not investment advice.
      </footer>
    </div>
  );
}
