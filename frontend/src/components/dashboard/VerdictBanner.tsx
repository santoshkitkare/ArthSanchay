import { formatINRShort } from "../../lib/money";
import type { ProjectionResult } from "../../types";

/** FR-VIZ-1: one plain-language sentence above the fold. */
export function VerdictBanner({ result }: { result: ProjectionResult }) {
  const { summary, meta } = result;
  const sustainable = summary.verdict === "sustainable";
  const severity = sustainable ? "good" : summary.years_short <= 5 ? "warn" : "bad";

  const message = sustainable
    ? `Your corpus lasts through age ${meta.life_expectancy}, with a terminal balance of ${formatINRShort(
        summary.terminal_corpus
      )}.`
    : `Your corpus runs out at age ${summary.exhaustion_age} — ${summary.years_short} year(s) short of age ${
        meta.life_expectancy
      }. Unfunded shortfall: ${formatINRShort(summary.unfunded_shortfall_today)} in today's rupees.`;

  return (
    <div className={`verdict-banner verdict-${severity}`} role="status">
      <strong>{sustainable ? "On track" : "Shortfall"}</strong>
      <span>{message}</span>
    </div>
  );
}
