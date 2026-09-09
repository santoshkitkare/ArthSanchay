import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { VerdictBanner } from "../components/dashboard/VerdictBanner";
import { MetricTiles } from "../components/dashboard/MetricTiles";
import { WhatIfStrip } from "../components/dashboard/WhatIfStrip";
import { SolverPanel } from "../components/dashboard/SolverPanel";
import { ProjectionTable } from "../components/dashboard/ProjectionTable";
import { CorpusTimelineChart } from "../components/charts/CorpusTimelineChart";
import { IncomeExpenseChart } from "../components/charts/IncomeExpenseChart";
import { useProjection, useScenario } from "../hooks/useProjection";
import type { ProjectionResult } from "../types";

export function ScenarioResultsPage() {
  const { id } = useParams();
  const scenarioId = Number(id);
  const { data: scenario } = useScenario(scenarioId);
  const { data: saved, isLoading, error } = useProjection(scenarioId);
  const [preview, setPreview] = useState<ProjectionResult | null>(null);

  if (isLoading || !saved || !scenario) return <div className="page">Loading…</div>;
  if (error) return <div className="page form-error">Could not load this scenario's projection.</div>;

  const shown = preview ?? saved;

  return (
    <div className="page">
      <header className="page-header">
        <h1>{scenario.name}</h1>
        <div>
          <Link to={`/scenarios/${scenarioId}/edit`}>Edit inputs</Link> · <Link to="/scenarios">All scenarios</Link>
        </div>
      </header>

      {preview && <div className="preview-badge">Showing an unsaved what-if preview</div>}

      <VerdictBanner result={shown} />
      <MetricTiles result={shown} />

      <section>
        <h2>Corpus over time</h2>
        <CorpusTimelineChart result={shown} />
      </section>

      <section>
        <h2>Income vs. expenses</h2>
        <IncomeExpenseChart result={shown} />
      </section>

      <WhatIfStrip scenario={scenario} onPreview={setPreview} />

      <SolverPanel scenarioId={scenarioId} />

      <ProjectionTable result={shown} />

      <footer className="disclaimer">
        This is an illustrative projection based on your own assumptions, not investment advice.
      </footer>
    </div>
  );
}
