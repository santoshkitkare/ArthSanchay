import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";
import { useDeleteScenario, useDuplicateScenario, useScenarioList } from "../hooks/useProjection";
import { scenariosApi } from "../api/scenarios";
import { formatDate } from "../lib/date";

export function ScenarioListPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { data: scenarios, isLoading, error } = useScenarioList();
  const deleteMutation = useDeleteScenario();
  const duplicateMutation = useDuplicateScenario();
  const [creating, setCreating] = useState(false);

  const createScenario = async () => {
    setCreating(true);
    try {
      const name = window.prompt("Scenario name", "Base case");
      if (!name) return;
      const scenario = await scenariosApi.create({ name });
      navigate(`/scenarios/${scenario.id}/edit`);
    } finally {
      setCreating(false);
    }
  };

  return (
    <div className="page">
      <header className="page-header">
        <h1>Your scenarios</h1>
        <div>
          <span className="muted">{user?.email}</span>{" "}
          <button type="button" onClick={() => logout()}>
            Log out
          </button>
        </div>
      </header>

      <button type="button" onClick={createScenario} disabled={creating}>
        + New scenario
      </button>

      {isLoading && <p>Loading…</p>}
      {error && <p className="form-error">Could not load scenarios.</p>}

      <ul className="scenario-list">
        {scenarios?.map((s) => (
          <li key={s.id} className="scenario-list-item">
            <Link to={`/scenarios/${s.id}`}>
              <strong>{s.name}</strong>
              <span className={`verdict-pill verdict-${s.verdict === "sustainable" ? "good" : "bad"}`}>
                {s.verdict === "sustainable" ? "On track" : `Short by ${s.years_short}y`}
              </span>
            </Link>
            <div className="scenario-list-actions">
              <span className="muted">Updated {formatDate(s.updated_at)}</span>
              <Link to={`/scenarios/${s.id}/edit`}>Edit</Link>
              <button type="button" onClick={() => duplicateMutation.mutate(s.id)}>
                Duplicate
              </button>
              <button
                type="button"
                onClick={() => {
                  if (window.confirm(`Delete "${s.name}"? This cannot be undone.`)) {
                    deleteMutation.mutate(s.id);
                  }
                }}
              >
                Delete
              </button>
            </div>
          </li>
        ))}
      </ul>
      {scenarios?.length === 0 && <p>No scenarios yet — create your first one above.</p>}
    </div>
  );
}
