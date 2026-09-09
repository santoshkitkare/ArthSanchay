import { formatINRShort, formatPercent } from "../../lib/money";
import type { ProjectionResult } from "../../types";

/** FR-VIZ-6: six key metrics in lakh/crore short form. */
export function MetricTiles({ result }: { result: ProjectionResult }) {
  const s = result.summary;
  const tiles: { label: string; value: string; flag?: boolean }[] = [
    { label: "Corpus at retirement", value: formatINRShort(s.corpus_at_retirement) },
    { label: "Peak corpus", value: `${formatINRShort(s.peak_corpus)} (age ${s.peak_age})` },
    {
      label: s.exhaustion_age !== null ? "Exhaustion age" : "Terminal corpus",
      value: s.exhaustion_age !== null ? `Age ${s.exhaustion_age}` : formatINRShort(s.terminal_corpus),
    },
    { label: "Total lifetime withdrawals", value: formatINRShort(s.total_withdrawals) },
    { label: "Total investment return", value: formatINRShort(s.total_return) },
    {
      label: "First-year withdrawal rate",
      value: formatPercent(s.first_year_withdrawal_rate, 1),
      flag: parseFloat(s.first_year_withdrawal_rate) > 0.04,
    },
  ];

  return (
    <div className="metric-tiles">
      {tiles.map((t) => (
        <div key={t.label} className={`metric-tile${t.flag ? " metric-flag" : ""}`}>
          <div className="metric-label">{t.label}</div>
          <div className="metric-value">{t.value}</div>
          {t.flag && <div className="metric-note">Above the conventional 4% guideline</div>}
        </div>
      ))}
    </div>
  );
}
