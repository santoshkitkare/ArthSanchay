import { useFormContext } from "react-hook-form";
import { MoneyField } from "../MoneyField";
import { PercentField } from "../PercentField";
import type { ScenarioFormValues } from "../../../types";

/** Section C — Living expenses (PRD.md §4.3). */
export function ExpensesSection() {
  const { control, register, watch } = useFormContext<ScenarioFormValues>();
  const annual = watch("inputs.annual_expense_today");
  const monthly = annual ? (parseFloat(annual) / 12).toFixed(0) : "0";

  return (
    <fieldset className="form-section">
      <legend>Living expenses</legend>
      <MoneyField
        control={control}
        name="inputs.annual_expense_today"
        label="Annual household expense today"
        help={`Everything you spend in a year at today's prices, excluding child costs. (≈ ₹${Number(
          monthly
        ).toLocaleString("en-IN")}/month)`}
      />
      <PercentField
        control={control}
        name="inputs.expense_inflation"
        label="Household expense inflation"
        help="The rate at which your cost of living rises."
      />
      <label className="field-inline">
        <input type="checkbox" {...register("inputs.charge_household_expense_pre_retirement")} />
        <span>Charge household expense before retirement</span>
      </label>
      <MoneyField
        control={control}
        name="inputs.medical_expense_today"
        label="Medical / health expense today"
        help="Tracked separately because it inflates faster than general expenses."
      />
      <PercentField control={control} name="inputs.medical_inflation" label="Medical inflation" />
      <PercentField
        control={control}
        name="inputs.post_retirement_expense_factor"
        label="Post-retirement expense factor"
        help="100% keeps workbook parity; many households spend less after retiring."
      />
    </fieldset>
  );
}
