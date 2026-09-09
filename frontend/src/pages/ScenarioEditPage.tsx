import { useNavigate, useParams } from "react-router-dom";
import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { ScenarioForm } from "../components/forms/ScenarioForm";
import { scenariosApi } from "../api/scenarios";
import { useScenario } from "../hooks/useProjection";
import type { ScenarioFormValues } from "../types";
import { ApiError } from "../api/client";

export function ScenarioEditPage() {
  const { id } = useParams();
  const scenarioId = Number(id);
  const navigate = useNavigate();
  const qc = useQueryClient();
  const { data: scenario, isLoading } = useScenario(scenarioId);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (isLoading || !scenario) return <div className="page">Loading…</div>;

  const defaultValues: ScenarioFormValues = {
    name: scenario.name,
    inputs: scenario.inputs,
    dependents: scenario.dependents,
    goals: scenario.goals,
    income_streams: scenario.income_streams,
  };

  const handleSubmit = async (values: ScenarioFormValues) => {
    setSubmitting(true);
    setError(null);
    try {
      await scenariosApi.replace(scenarioId, values);
      await qc.invalidateQueries({ queryKey: ["scenario", scenarioId] });
      await qc.invalidateQueries({ queryKey: ["projection", scenarioId] });
      await qc.invalidateQueries({ queryKey: ["scenarios"] });
      navigate(`/scenarios/${scenarioId}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not save scenario");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="page">
      <h1>Edit scenario</h1>
      {error && <div className="form-error">{error}</div>}
      <ScenarioForm defaultValues={defaultValues} onSubmit={handleSubmit} submitting={submitting} />
    </div>
  );
}
