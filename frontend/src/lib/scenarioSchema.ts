import { z } from "zod";

// Mirrors the range constraints in backend/app/schemas/scenario.py (NFR-4: the backend is still
// the source of truth and re-validates everything; this is the client-side first pass so errors
// surface inline rather than only after a round trip).

const decimalString = z.string().refine((v) => v !== "" && !isNaN(parseFloat(v)), "Enter a number");
const nonNegativeDecimal = decimalString.refine((v) => parseFloat(v) >= 0, "Cannot be negative");

const dependentSchema = z
  .object({
    id: z.number().optional(),
    label: z.string().min(1, "Required").max(40),
    current_age: z.number().int().min(0).max(40),
    school_fee_today: nonNegativeDecimal,
    school_fee_hike: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.5, "0–50%"),
    school_fee_hike_frequency: z.number().int().min(1).max(10),
    school_end_age: z.number().int().min(10).max(30),
    graduation_cost_today: nonNegativeDecimal,
    graduation_inflation: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.2, "0–20%"),
    graduation_start_age: z.number().int().min(15).max(30),
    graduation_duration: z.number().int().min(1).max(8),
    inflate_graduation_instalments: z.boolean(),
    marriage_cost_today: nonNegativeDecimal,
    marriage_inflation: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.2, "0–20%"),
    marriage_age: z.number().int().min(18).max(45).nullable(),
    fund_school_from_corpus_pre_retirement: z.boolean(),
  })
  .refine((d) => d.marriage_age === null || d.marriage_age >= d.current_age, {
    message: "Marriage age cannot be before the dependent's current age",
    path: ["marriage_age"],
  });

const goalSchema = z.object({
  id: z.number().optional(),
  label: z.string().min(1).max(80),
  amount_today: nonNegativeDecimal,
  at_age: z.number().int().min(0).max(110),
  inflation: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.2, "0–20%"),
  recurrence: z.enum(["once", "annual", "every_n_years"]),
  recurrence_years: z.number().int().min(1).max(20).nullable(),
  duration_years: z.number().int().min(1).max(80).nullable(),
});

const incomeStreamSchema = z
  .object({
    id: z.number().optional(),
    label: z.string().min(1).max(80),
    monthly_amount_today: nonNegativeDecimal,
    start_age: z.number().int().min(0).max(110),
    end_age: z.number().int().min(0).max(110).nullable(),
    annual_escalation: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.2, "0–20%"),
  })
  .refine((i) => i.end_age === null || i.end_age >= i.start_age, {
    message: "End age cannot be before start age",
    path: ["end_age"],
  });

const scenarioInputsSchema = z
  .object({
    current_age: z.number().int().min(18).max(75),
    retirement_age: z.number().int().min(18).max(110),
    life_expectancy: z.number().int().min(19).max(110),
    plan_start_year: z.number().int().min(1900).max(2200),
    current_corpus: nonNegativeDecimal,
    monthly_contribution: nonNegativeDecimal,
    contribution_stepup: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.25, "0–25%"),
    contributions_stop_age: z.number().int().min(0).max(110).nullable(),
    pre_retirement_return: decimalString.refine((v) => parseFloat(v) >= -0.2 && parseFloat(v) <= 0.4, "-20% to 40%"),
    post_retirement_return: decimalString.refine((v) => parseFloat(v) >= -0.2 && parseFloat(v) <= 0.4, "-20% to 40%"),
    annual_expense_today: nonNegativeDecimal,
    expense_inflation: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.2, "0–20%"),
    charge_household_expense_pre_retirement: z.boolean(),
    medical_expense_today: nonNegativeDecimal,
    medical_inflation: decimalString.refine((v) => parseFloat(v) >= 0 && parseFloat(v) <= 0.25, "0–25%"),
    post_retirement_expense_factor: decimalString.refine(
      (v) => parseFloat(v) >= 0.3 && parseFloat(v) <= 1.5,
      "30–150%"
    ),
    engine_mode: z.enum(["monthly", "annual_parity"]),
  })
  .refine((i) => i.retirement_age >= i.current_age, {
    message: "Retirement age cannot be before current age",
    path: ["retirement_age"],
  })
  .refine((i) => i.life_expectancy > i.retirement_age, {
    message: "Life expectancy must be after retirement age",
    path: ["life_expectancy"],
  });

export const scenarioFormSchema = z.object({
  name: z.string().min(1, "Required").max(120),
  inputs: scenarioInputsSchema,
  dependents: z.array(dependentSchema),
  goals: z.array(goalSchema),
  income_streams: z.array(incomeStreamSchema),
});
