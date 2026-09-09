import type { ProjectionRow } from "../types";

export interface AnnualPoint {
  age: number;
  year: number;
  corpus_start: number;
  corpus_end: number;
  corpus_end_today_rupees: number;
  household: number;
  medical: number;
  school: number;
  graduation: number;
  marriage: number;
  custom: number;
  inflow_contribution: number;
  inflow_income: number;
  investment_return: number;
  shortfall: number;
}

const n = (s: string) => parseFloat(s);

/** Collapse monthly rows to one point per plan year — the year's last corpus_end snapshot, and
 * the year's summed flows. Rows already at annual granularity (annual_parity mode) pass through
 * unchanged, one point per row.
 */
export function aggregateToAnnual(rows: ProjectionRow[]): AnnualPoint[] {
  const byAge = new Map<number, ProjectionRow[]>();
  for (const row of rows) {
    const list = byAge.get(row.age) ?? [];
    list.push(row);
    byAge.set(row.age, list);
  }
  const ages = [...byAge.keys()].sort((a, b) => a - b);
  return ages.map((age) => {
    const group = byAge.get(age)!;
    const first = group[0];
    const last = group[group.length - 1];
    const sum = (key: keyof ProjectionRow) => group.reduce((acc, r) => acc + n(r[key] as string), 0);
    return {
      age,
      year: last.year,
      corpus_start: n(first.corpus_start),
      corpus_end: n(last.corpus_end),
      corpus_end_today_rupees: n(last.corpus_end_today_rupees),
      household: sum("household"),
      medical: sum("medical"),
      school: sum("school"),
      graduation: sum("graduation"),
      marriage: sum("marriage"),
      custom: sum("custom"),
      inflow_contribution: sum("inflow_contribution"),
      inflow_income: sum("inflow_income"),
      investment_return: sum("investment_return"),
      shortfall: sum("shortfall"),
    };
  });
}
