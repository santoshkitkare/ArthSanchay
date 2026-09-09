import { useFieldArray, useFormContext } from "react-hook-form";
import { MoneyField } from "../MoneyField";
import { PercentField } from "../PercentField";
import type { ScenarioFormValues } from "../../../types";

const BLANK_DEPENDENT = {
  label: "New child",
  current_age: 0,
  school_fee_today: "0",
  school_fee_hike: "0.25",
  school_fee_hike_frequency: 2,
  school_end_age: 18,
  graduation_cost_today: "0",
  graduation_inflation: "0.07",
  graduation_start_age: 18,
  graduation_duration: 4,
  inflate_graduation_instalments: true,
  marriage_cost_today: "0",
  marriage_inflation: "0.07",
  marriage_age: null,
  fund_school_from_corpus_pre_retirement: true,
};

/** Section D — Dependents (replaces the workbook's hardcoded Son/Daughter columns). */
export function DependentsSection() {
  const { control, register, watch } = useFormContext<ScenarioFormValues>();
  const { fields, append, remove } = useFieldArray({ control, name: "dependents" });

  return (
    <fieldset className="form-section">
      <legend>Dependents</legend>
      {fields.map((field, index) => {
        const hike = watch(`dependents.${index}.school_fee_hike`);
        const freq = watch(`dependents.${index}.school_fee_hike_frequency`);
        const effectiveAnnual = hike && freq ? (Math.pow(1 + parseFloat(hike), 1 / freq) - 1) * 100 : 0;

        return (
          <div key={field.id} className="repeater-item">
            <div className="repeater-header">
              <input {...register(`dependents.${index}.label`)} placeholder="Name" />
              <button type="button" onClick={() => remove(index)}>
                Remove
              </button>
            </div>
            <label className="field">
              <span className="field-label">Current age</span>
              <input type="number" {...register(`dependents.${index}.current_age`, { valueAsNumber: true })} />
            </label>
            <MoneyField control={control} name={`dependents.${index}.school_fee_today`} label="Annual school fee today" />
            <PercentField
              control={control}
              name={`dependents.${index}.school_fee_hike`}
              label="School fee hike"
              help={`Effective ≈ ${effectiveAnnual.toFixed(1)}% per year, given the frequency below.`}
            />
            <label className="field">
              <span className="field-label">School fee hike frequency (years)</span>
              <input
                type="number"
                {...register(`dependents.${index}.school_fee_hike_frequency`, { valueAsNumber: true })}
              />
            </label>
            <label className="field">
              <span className="field-label">Schooling ends at age</span>
              <input type="number" {...register(`dependents.${index}.school_end_age`, { valueAsNumber: true })} />
            </label>
            <MoneyField
              control={control}
              name={`dependents.${index}.graduation_cost_today`}
              label="Graduation total cost today"
            />
            <PercentField control={control} name={`dependents.${index}.graduation_inflation`} label="Graduation inflation" />
            <label className="field">
              <span className="field-label">Graduation start age</span>
              <input
                type="number"
                {...register(`dependents.${index}.graduation_start_age`, { valueAsNumber: true })}
              />
            </label>
            <label className="field">
              <span className="field-label">Graduation duration (years)</span>
              <input
                type="number"
                {...register(`dependents.${index}.graduation_duration`, { valueAsNumber: true })}
              />
            </label>
            <label className="field-inline">
              <input type="checkbox" {...register(`dependents.${index}.inflate_graduation_instalments`)} />
              <span>Inflate each graduation instalment (off reproduces the original workbook)</span>
            </label>
            <MoneyField control={control} name={`dependents.${index}.marriage_cost_today`} label="Marriage cost today" />
            <PercentField control={control} name={`dependents.${index}.marriage_inflation`} label="Marriage inflation" />
            <label className="field">
              <span className="field-label">Marriage age (blank to exclude)</span>
              <input
                type="number"
                {...register(`dependents.${index}.marriage_age`, {
                  setValueAs: (v) => (v === "" ? null : Number(v)),
                })}
              />
            </label>
            <label className="field-inline">
              <input type="checkbox" {...register(`dependents.${index}.fund_school_from_corpus_pre_retirement`)} />
              <span>Fund school fees from corpus before retirement</span>
            </label>
          </div>
        );
      })}
      <button type="button" onClick={() => append(BLANK_DEPENDENT)}>
        + Add dependent
      </button>
    </fieldset>
  );
}
