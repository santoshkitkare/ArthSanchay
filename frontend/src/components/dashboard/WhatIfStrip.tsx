import { useEffect, useRef, useState } from "react";
import { formatPercent } from "../../lib/money";
import type { ProjectionResult, Scenario } from "../../types";
import { useWhatIfProjection } from "../../hooks/useProjection";

interface Props {
  scenario: Scenario;
  onPreview: (result: ProjectionResult | null) => void;
}

/** §8.3's what-if slider strip: retirement age / SIP / returns / inflation, debounced 250ms,
 * running a transient (unsaved) projection so the chart updates live as the user drags.
 */
export function WhatIfStrip({ scenario, onPreview }: Props) {
  const inp = scenario.inputs;
  const [retirementAge, setRetirementAge] = useState(inp.retirement_age);
  const [sip, setSip] = useState(parseFloat(inp.monthly_contribution));
  const [preReturn, setPreReturn] = useState(parseFloat(inp.pre_retirement_return) * 100);
  const [inflation, setInflation] = useState(parseFloat(inp.expense_inflation) * 100);
  const [dirty, setDirty] = useState(false);

  const mutation = useWhatIfProjection(scenario.id);
  const debounceRef = useRef<number | undefined>(undefined);

  useEffect(() => {
    if (!dirty) return;
    window.clearTimeout(debounceRef.current);
    debounceRef.current = window.setTimeout(() => {
      mutation.mutate(
        {
          inputs: {
            retirement_age: retirementAge,
            monthly_contribution: String(sip),
            pre_retirement_return: String(preReturn / 100),
            expense_inflation: String(inflation / 100),
          },
        },
        { onSuccess: (result) => onPreview(result) }
      );
    }, 250);
    return () => window.clearTimeout(debounceRef.current);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [retirementAge, sip, preReturn, inflation, dirty]);

  const reset = () => {
    setRetirementAge(inp.retirement_age);
    setSip(parseFloat(inp.monthly_contribution));
    setPreReturn(parseFloat(inp.pre_retirement_return) * 100);
    setInflation(parseFloat(inp.expense_inflation) * 100);
    setDirty(false);
    onPreview(null);
  };

  const mark = (setter: (v: number) => void) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setter(Number(e.target.value));
    setDirty(true);
  };

  return (
    <div className="what-if-strip">
      <h3>What if…</h3>
      <div className="what-if-grid">
        <label>
          Retirement age: <strong>{retirementAge}</strong>
          <input
            type="range"
            min={inp.current_age}
            max={inp.life_expectancy - 1}
            value={retirementAge}
            onChange={mark((v) => setRetirementAge(v))}
          />
        </label>
        <label>
          Monthly SIP: <strong>₹{sip.toLocaleString("en-IN")}</strong>
          <input type="range" min={0} max={500000} step={1000} value={sip} onChange={mark((v) => setSip(v))} />
        </label>
        <label>
          Pre-retirement return: <strong>{formatPercent(preReturn / 100, 1)}</strong>
          <input
            type="range"
            min={-5}
            max={20}
            step={0.5}
            value={preReturn}
            onChange={mark((v) => setPreReturn(v))}
          />
        </label>
        <label>
          Expense inflation: <strong>{formatPercent(inflation / 100, 1)}</strong>
          <input type="range" min={0} max={15} step={0.5} value={inflation} onChange={mark((v) => setInflation(v))} />
        </label>
      </div>
      {dirty && (
        <div className="what-if-actions">
          {mutation.isPending && <span>Recalculating…</span>}
          <button type="button" onClick={reset}>
            Reset to saved
          </button>
        </div>
      )}
    </div>
  );
}
