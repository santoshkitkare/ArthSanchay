import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { scenariosApi } from "../api/scenarios";
import type { ProjectionOverrides, SolverTarget } from "../types";

export function useScenarioList() {
  return useQuery({ queryKey: ["scenarios"], queryFn: scenariosApi.list });
}

export function useScenario(id: number | undefined) {
  return useQuery({
    queryKey: ["scenario", id],
    queryFn: () => scenariosApi.get(id as number),
    enabled: id !== undefined,
  });
}

/** The saved-state projection for a scenario: what the results dashboard shows on load. */
export function useProjection(id: number | undefined) {
  return useQuery({
    queryKey: ["projection", id],
    queryFn: () => scenariosApi.project(id as number),
    enabled: id !== undefined,
  });
}

/** Transient what-if projection (§8.3's slider strip) — never persisted, invoked on demand. */
export function useWhatIfProjection(id: number) {
  return useMutation({
    mutationFn: (overrides: ProjectionOverrides) => scenariosApi.project(id, overrides),
  });
}

export function useSolve(id: number) {
  return useMutation({
    mutationFn: (target: SolverTarget) => scenariosApi.solve(id, target),
  });
}

export function useDeleteScenario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => scenariosApi.remove(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenarios"] }),
  });
}

export function useDuplicateScenario() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => scenariosApi.duplicate(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["scenarios"] }),
  });
}
