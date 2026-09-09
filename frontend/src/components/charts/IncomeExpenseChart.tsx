import { Bar } from "react-chartjs-2";
import "./chartSetup";
import { aggregateToAnnual } from "../../lib/aggregate";
import { formatINRShort } from "../../lib/money";
import type { ProjectionResult } from "../../types";

/** FR-VIZ-3: every category stacks upward from a zero baseline at the bottom, colour-coded by
 * category (contributions/income vs. each expense category) so the total height at any age reads
 * as "how much moved that year" and the segments read as "on what". An earlier version put
 * expenses below the axis and income above it; with income/contributions at zero (the common
 * case — the workbook itself has none), that left the zero baseline pinned to the top of the
 * chart with every bar hanging downward from it, which read as upside down. Colour still
 * distinguishes inflow from outflow categories via the legend.
 */
export function IncomeExpenseChart({ result }: { result: ProjectionResult }) {
  const points = aggregateToAnnual(result.rows);

  const data = {
    labels: points.map((p) => p.age),
    datasets: [
      {
        label: "Contributions",
        data: points.map((p) => p.inflow_contribution),
        backgroundColor: "#16a34a",
        stack: "flow",
      },
      {
        label: "Income",
        data: points.map((p) => p.inflow_income),
        backgroundColor: "#4ade80",
        stack: "flow",
      },
      {
        label: "Household & medical",
        data: points.map((p) => p.household + p.medical),
        backgroundColor: "#2563eb",
        stack: "flow",
      },
      {
        label: "School fees",
        data: points.map((p) => p.school),
        backgroundColor: "#f59e0b",
        stack: "flow",
      },
      {
        label: "Graduation",
        data: points.map((p) => p.graduation),
        backgroundColor: "#14b8a6",
        stack: "flow",
      },
      {
        label: "Marriage",
        data: points.map((p) => p.marriage),
        backgroundColor: "#ec4899",
        stack: "flow",
      },
      {
        label: "Other goals",
        data: points.map((p) => p.custom),
        backgroundColor: "#6b7280",
        stack: "flow",
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: "index" as const, intersect: false },
    plugins: {
      legend: { position: "bottom" as const, labels: { boxWidth: 12 } },
      tooltip: {
        callbacks: {
          title: (items: { label: string }[]) => `Age ${items[0].label}`,
          label: (item: { dataset: { label?: string }; parsed: { y: number | null } }) =>
            `${item.dataset.label}: ${formatINRShort(item.parsed.y ?? 0)}`,
        },
      },
    },
    scales: {
      x: { stacked: true, title: { display: true, text: "Age" } },
      y: {
        stacked: true,
        beginAtZero: true,
        title: { display: true, text: "Money in / money out" },
        ticks: { callback: (v: string | number) => formatINRShort(Number(v)) },
      },
    },
  };

  return (
    <div style={{ height: 320 }}>
      <Bar data={data} options={options} />
    </div>
  );
}
