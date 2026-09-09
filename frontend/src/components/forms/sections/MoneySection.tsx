import { useFormContext } from "react-hook-form";
import { MoneyField } from "../MoneyField";
import { PercentField } from "../PercentField";
import type { ScenarioFormValues } from "../../../types";

/** Section B — Money you have and money you add (PRD.md §4.3). */
export function MoneySection() {
  const {
    control,
    register,
    formState: { errors },
  } = useFormContext<ScenarioFormValues>();
  const e = errors.inputs;

  return (
    <fieldset className="form-section">
      <legend>Money you have and add</legend>
      <MoneyField
        control={control}
        name="inputs.current_corpus"
        label="Current corpus"
        help="Everything invested today: equity, debt, EPF, PPF, NPS, deposits. Exclude the home you live in."
        error={e?.current_corpus?.message}
      />
      <MoneyField
        control={control}
        name="inputs.monthly_contribution"
        label="Monthly contribution (SIP)"
        help="What you invest every month from income."
      />
      <PercentField
        control={control}
        name="inputs.contribution_stepup"
        label="Annual step-up on contribution"
        help="Increase your SIP by this much each year, typically in line with salary growth."
      />
      <label className="field">
        <span className="field-label">Contributions stop at age</span>
        <input
          type="number"
          placeholder="defaults to retirement age"
          {...register("inputs.contributions_stop_age", {
            setValueAs: (v) => (v === "" ? null : Number(v)),
          })}
        />
      </label>
      <PercentField
        control={control}
        name="inputs.pre_retirement_return"
        label="Pre-retirement return"
        help="Expected annual return while still working. Enter a figure net of tax and fees."
        error={e?.pre_retirement_return?.message}
      />
      <PercentField
        control={control}
        name="inputs.post_retirement_return"
        label="Post-retirement return"
        help="Expected return after retiring — usually lower, as the portfolio de-risks."
        error={e?.post_retirement_return?.message}
      />
      <label className="field">
        <span className="field-label">Engine mode</span>
        <select {...register("inputs.engine_mode")}>
          <option value="monthly">Monthly (recommended)</option>
          <option value="annual_parity">Annual (matches the original workbook)</option>
        </select>
      </label>
    </fieldset>
  );
}
