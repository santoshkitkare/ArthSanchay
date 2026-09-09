import { useFieldArray, useFormContext } from "react-hook-form";
import { MoneyField } from "../MoneyField";
import { PercentField } from "../PercentField";
import type { ScenarioFormValues } from "../../../types";

const BLANK_GOAL = {
  label: "New goal",
  amount_today: "0",
  at_age: 50,
  inflation: "0.07",
  recurrence: "once" as const,
  recurrence_years: null,
  duration_years: null,
};

const BLANK_INCOME = {
  label: "New income",
  monthly_amount_today: "0",
  start_age: 60,
  end_age: null,
  annual_escalation: "0",
};

/** Section E — Custom goals and other income (new; PRD.md §4.3). */
export function GoalsIncomeSection() {
  const { control, register, watch } = useFormContext<ScenarioFormValues>();
  const goals = useFieldArray({ control, name: "goals" });
  const income = useFieldArray({ control, name: "income_streams" });

  return (
    <fieldset className="form-section">
      <legend>Custom goals and other income</legend>

      <h4>Goals</h4>
      {goals.fields.map((field, index) => {
        const recurrence = watch(`goals.${index}.recurrence`);
        return (
          <div key={field.id} className="repeater-item">
            <div className="repeater-header">
              <input {...register(`goals.${index}.label`)} placeholder="Label" />
              <button type="button" onClick={() => goals.remove(index)}>
                Remove
              </button>
            </div>
            <MoneyField control={control} name={`goals.${index}.amount_today`} label="Amount today" />
            <label className="field">
              <span className="field-label">At your age</span>
              <input type="number" {...register(`goals.${index}.at_age`, { valueAsNumber: true })} />
            </label>
            <PercentField control={control} name={`goals.${index}.inflation`} label="Inflation" />
            <label className="field">
              <span className="field-label">Recurrence</span>
              <select {...register(`goals.${index}.recurrence`)}>
                <option value="once">Once</option>
                <option value="annual">Every year</option>
                <option value="every_n_years">Every N years</option>
              </select>
            </label>
            {recurrence === "every_n_years" && (
              <label className="field">
                <span className="field-label">Every N years</span>
                <input
                  type="number"
                  {...register(`goals.${index}.recurrence_years`, {
                    setValueAs: (v) => (v === "" ? null : Number(v)),
                  })}
                />
              </label>
            )}
            {recurrence !== "once" && (
              <label className="field">
                <span className="field-label">Duration (years, blank = until life expectancy)</span>
                <input
                  type="number"
                  {...register(`goals.${index}.duration_years`, {
                    setValueAs: (v) => (v === "" ? null : Number(v)),
                  })}
                />
              </label>
            )}
          </div>
        );
      })}
      <button type="button" onClick={() => goals.append(BLANK_GOAL)}>
        + Add goal
      </button>

      <h4>Other income</h4>
      {income.fields.map((field, index) => (
        <div key={field.id} className="repeater-item">
          <div className="repeater-header">
            <input {...register(`income_streams.${index}.label`)} placeholder="Label" />
            <button type="button" onClick={() => income.remove(index)}>
              Remove
            </button>
          </div>
          <MoneyField
            control={control}
            name={`income_streams.${index}.monthly_amount_today`}
            label="Monthly amount today"
          />
          <label className="field">
            <span className="field-label">Start age</span>
            <input type="number" {...register(`income_streams.${index}.start_age`, { valueAsNumber: true })} />
          </label>
          <label className="field">
            <span className="field-label">End age (blank = life expectancy)</span>
            <input
              type="number"
              {...register(`income_streams.${index}.end_age`, {
                setValueAs: (v) => (v === "" ? null : Number(v)),
              })}
            />
          </label>
          <PercentField control={control} name={`income_streams.${index}.annual_escalation`} label="Annual escalation" />
        </div>
      ))}
      <button type="button" onClick={() => income.append(BLANK_INCOME)}>
        + Add income stream
      </button>
    </fieldset>
  );
}
