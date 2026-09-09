import { Line } from "react-chartjs-2";
import "./chartSetup";
import { aggregateToAnnual } from "../../lib/aggregate";
import { formatINRShort } from "../../lib/money";
import type { ProjectionResult } from "../../types";

/** FR-VIZ-2: corpus balance as a filled area against age, with markers at retirement and
 * exhaustion (when the plan falls short). This is the single chart the whole product exists to
 * put in front of the user — the workbook never had one.
 */
export function CorpusTimelineChart({ result }: { result: ProjectionResult }) {
  const points = aggregateToAnnual(result.rows);
  const { retirement_age, life_expectancy } = result.meta;
  const exhaustionAge = result.summary.exhaustion_age;

  const data = {
    labels: points.map((p) => p.age),
    datasets: [
      {
        label: "Corpus balance",
        data: points.map((p) => p.corpus_end),
        borderColor: "#2563eb",
        backgroundColor: "rgba(37, 99, 235, 0.15)",
        fill: true,
        tension: 0.15,
        pointRadius: 0,
        pointHitRadius: 12,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: { display: false },
      tooltip: {
        callbacks: {
          title: (items: { label: string }[]) => `Age ${items[0].label}`,
          label: (item: { parsed: { y: number | null } }) => `Corpus: ${formatINRShort(item.parsed.y ?? 0)}`,
        },
      },
    },
    scales: {
      x: { title: { display: true, text: "Age" } },
      y: {
        title: { display: true, text: "Corpus balance" },
        ticks: { callback: (v: string | number) => formatINRShort(v) },
      },
    },
  };

  return (
    <div style={{ position: "relative", height: 320 }}>
      <Line data={data} options={options} />
      <div className="chart-markers" aria-hidden="true">
        {/* Text-based markers below the chart, since color alone must not carry the meaning
            (§8.4) — a compact legend rather than an overlaid annotation plugin. */}
      </div>
      <div className="chart-legend-text">
        <span className="marker retirement">● Retirement at age {retirement_age}</span>
        {exhaustionAge !== null ? (
          <span className="marker exhaustion">● Corpus exhausted at age {exhaustionAge}</span>
        ) : (
          <span className="marker sustainable">● Sustainable through age {life_expectancy}</span>
        )}
      </div>
    </div>
  );
}
