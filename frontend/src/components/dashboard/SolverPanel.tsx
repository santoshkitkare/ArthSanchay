import { useState } from "react";
import { formatINRShort } from "../../lib/money";
import type { SolveResult, SolverTarget } from "../../types";
import { useSolve } from "../../hooks/useProjection";

const LABELS: Record<SolverTarget, string> = {
  required_corpus: "Required corpus at retirement",
  required_contribution: "Required monthly SIP",
  longevity: "How long does it last?",
};

/** §8.3's solver panel — FR-SOL-1/2/3. */
export function SolverPanel({ scenarioId }: { scenarioId: number }) {
  const solve = useSolve(scenarioId);
  const [results, setResults] = useState<Partial<Record<SolverTarget, SolveResult>>>({});

  const run = (target: SolverTarget) => {
    solve.mutate(target, { onSuccess: (result) => setResults((prev) => ({ ...prev, [target]: result })) });
  };

  return (
    <div className="solver-panel">
      <h3>What do I need?</h3>
      <div className="solver-buttons">
        {(Object.keys(LABELS) as SolverTarget[]).map((target) => (
          <button key={target} type="button" onClick={() => run(target)} disabled={solve.isPending}>
            {LABELS[target]}
          </button>
        ))}
      </div>
      <div className="solver-results">
        {(Object.keys(results) as SolverTarget[]).map((target) => {
          const r = results[target]!;
          return (
            <div key={target} className="solver-result">
              <strong>{LABELS[target]}:</strong>{" "}
              {!r.feasible ? (
                <span>{r.message}</span>
              ) : target === "longevity" ? (
                <span>{r.message}</span>
              ) : (
                <span>
                  {formatINRShort(r.value ?? "0")}
                  {r.gap_vs_current !== null && (
                    <>
                      {" "}
                      (gap: {parseFloat(r.gap_vs_current) >= 0 ? "+" : ""}
                      {formatINRShort(r.gap_vs_current)})
                    </>
                  )}
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
