import { useFormContext } from "react-hook-form";
import type { ScenarioFormValues } from "../../../types";

/** Section A — You and your timeline (PRD.md §4.3). */
export function TimelineSection() {
  const {
    register,
    formState: { errors },
  } = useFormContext<ScenarioFormValues>();
  const e = errors.inputs;

  return (
    <fieldset className="form-section">
      <legend>You and your timeline</legend>
      <label className="field">
        <span className="field-label">Current age</span>
        <input type="number" {...register("inputs.current_age", { valueAsNumber: true })} />
        <span className="field-help">Your age today.</span>
        {e?.current_age && <span className="field-error">{e.current_age.message}</span>}
      </label>
      <label className="field">
        <span className="field-label">Retirement age</span>
        <input type="number" {...register("inputs.retirement_age", { valueAsNumber: true })} />
        <span className="field-help">The age at which you stop earning a salary.</span>
        {e?.retirement_age && <span className="field-error">{e.retirement_age.message}</span>}
      </label>
      <label className="field">
        <span className="field-label">Life expectancy</span>
        <input type="number" {...register("inputs.life_expectancy", { valueAsNumber: true })} />
        <span className="field-help">Plan to a conservative age — outliving the plan is the risk that matters.</span>
        {e?.life_expectancy && <span className="field-error">{e.life_expectancy.message}</span>}
      </label>
      <label className="field">
        <span className="field-label">Plan start year</span>
        <input type="number" {...register("inputs.plan_start_year", { valueAsNumber: true })} />
      </label>
    </fieldset>
  );
}
