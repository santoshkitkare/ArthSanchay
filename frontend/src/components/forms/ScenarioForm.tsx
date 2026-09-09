import { zodResolver } from "@hookform/resolvers/zod";
import { FormProvider, useForm } from "react-hook-form";
import { DependentsSection } from "./sections/DependentsSection";
import { ExpensesSection } from "./sections/ExpensesSection";
import { GoalsIncomeSection } from "./sections/GoalsIncomeSection";
import { MoneySection } from "./sections/MoneySection";
import { TimelineSection } from "./sections/TimelineSection";
import { scenarioFormSchema } from "../../lib/scenarioSchema";
import type { ScenarioFormValues } from "../../types";

interface Props {
  defaultValues: ScenarioFormValues;
  onSubmit: (values: ScenarioFormValues) => void;
  submitting?: boolean;
}

/** The five-section input model (PRD.md §4.3), assembled as one form. Each section validates
 * independently (its own fieldset, its own error messages) even though they submit together —
 * a deliberate simplification of the PRD's multi-step wizard for this pass: one scrollable,
 * fully-validated edit page rather than a stepper with per-section autosave.
 */
export function ScenarioForm({ defaultValues, onSubmit, submitting }: Props) {
  const methods = useForm<ScenarioFormValues>({
    resolver: zodResolver(scenarioFormSchema),
    defaultValues,
    mode: "onBlur",
  });

  return (
    <FormProvider {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className="scenario-form">
        <label className="field">
          <span className="field-label">Scenario name</span>
          <input {...methods.register("name")} />
          {methods.formState.errors.name && (
            <span className="field-error">{methods.formState.errors.name.message}</span>
          )}
        </label>

        <TimelineSection />
        <MoneySection />
        <ExpensesSection />
        <DependentsSection />
        <GoalsIncomeSection />

        <div className="form-actions">
          <button type="submit" disabled={submitting}>
            {submitting ? "Saving…" : "Save scenario"}
          </button>
        </div>
      </form>
    </FormProvider>
  );
}
