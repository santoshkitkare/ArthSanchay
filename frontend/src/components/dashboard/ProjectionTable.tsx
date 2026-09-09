import { useState } from "react";
import { aggregateToAnnual } from "../../lib/aggregate";
import { formatINR } from "../../lib/money";
import type { ProjectionResult } from "../../types";

/** FR-VIZ-7: the full grid. Annual by default (readable row count); monthly toggle available.
 * ~456 rows renders fine without row virtualization (a deliberate simplification — see the
 * implementation plan).
 */
export function ProjectionTable({ result }: { result: ProjectionResult }) {
  const [monthly, setMonthly] = useState(false);
  const annualRows = aggregateToAnnual(result.rows);

  return (
    <div className="projection-table-wrap">
      <div className="table-controls">
        <h3>Projection</h3>
        <label>
          <input type="checkbox" checked={monthly} onChange={(e) => setMonthly(e.target.checked)} /> Show monthly
        </label>
      </div>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>{monthly ? "Month" : "Age"}</th>
              {monthly && <th>Age</th>}
              <th>Corpus start</th>
              <th>Household</th>
              <th>Medical</th>
              <th>School</th>
              <th>Graduation</th>
              <th>Marriage</th>
              <th>Other</th>
              <th>Contribution</th>
              <th>Income</th>
              <th>Return</th>
              <th>Corpus end</th>
              <th>Shortfall</th>
            </tr>
          </thead>
          <tbody>
            {monthly
              ? result.rows.map((r) => (
                  <tr key={r.t} className={parseFloat(r.shortfall) > 0 ? "row-shortfall" : undefined}>
                    <td>
                      {r.year}-{String(r.month + 1).padStart(2, "0")}
                    </td>
                    <td>{r.age}</td>
                    <td>{formatINR(r.corpus_start)}</td>
                    <td>{formatINR(r.household)}</td>
                    <td>{formatINR(r.medical)}</td>
                    <td>{formatINR(r.school)}</td>
                    <td>{formatINR(r.graduation)}</td>
                    <td>{formatINR(r.marriage)}</td>
                    <td>{formatINR(r.custom)}</td>
                    <td>{formatINR(r.inflow_contribution)}</td>
                    <td>{formatINR(r.inflow_income)}</td>
                    <td>{formatINR(r.investment_return)}</td>
                    <td>{formatINR(r.corpus_end)}</td>
                    <td>{parseFloat(r.shortfall) > 0 ? formatINR(r.shortfall) : "—"}</td>
                  </tr>
                ))
              : annualRows.map((r) => (
                  <tr key={r.age} className={r.shortfall > 0 ? "row-shortfall" : undefined}>
                    <td>{r.age}</td>
                    <td>{formatINR(r.corpus_start)}</td>
                    <td>{formatINR(r.household)}</td>
                    <td>{formatINR(r.medical)}</td>
                    <td>{formatINR(r.school)}</td>
                    <td>{formatINR(r.graduation)}</td>
                    <td>{formatINR(r.marriage)}</td>
                    <td>{formatINR(r.custom)}</td>
                    <td>{formatINR(r.inflow_contribution)}</td>
                    <td>{formatINR(r.inflow_income)}</td>
                    <td>{formatINR(r.investment_return)}</td>
                    <td>{formatINR(r.corpus_end)}</td>
                    <td>{r.shortfall > 0 ? formatINR(r.shortfall) : "—"}</td>
                  </tr>
                ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
