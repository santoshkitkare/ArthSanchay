import { api } from "./client";
import type {
  Dependent,
  Goal,
  IncomeStream,
  ProjectionOverrides,
  ProjectionResult,
  Scenario,
  ScenarioInputs,
  ScenarioListItem,
  SolveResult,
  SolverTarget,
} from "../types";

export interface ScenarioCreatePayload {
  name: string;
  inputs?: ScenarioInputs;
  dependents?: Dependent[];
  goals?: Goal[];
  income_streams?: IncomeStream[];
}

export interface ScenarioReplacePayload {
  name: string;
  inputs: ScenarioInputs;
  dependents: Dependent[];
  goals: Goal[];
  income_streams: IncomeStream[];
}

export const scenariosApi = {
  list: () => api.get<ScenarioListItem[]>("/api/scenarios"),
  create: (payload: ScenarioCreatePayload) => api.post<Scenario>("/api/scenarios", payload),
  get: (id: number) => api.get<Scenario>(`/api/scenarios/${id}`),
  replace: (id: number, payload: ScenarioReplacePayload) => api.put<Scenario>(`/api/scenarios/${id}`, payload),
  patch: (id: number, payload: Partial<ScenarioReplacePayload>) =>
    api.patch<Scenario>(`/api/scenarios/${id}`, payload),
  remove: (id: number) => api.delete<void>(`/api/scenarios/${id}`),
  duplicate: (id: number) => api.post<Scenario>(`/api/scenarios/${id}/duplicate`),
  project: (id: number, overrides?: ProjectionOverrides) =>
    api.post<ProjectionResult>(`/api/scenarios/${id}/project`, overrides ?? {}),
  solve: (id: number, target: SolverTarget, desiredLegacy = "0") =>
    api.post<SolveResult>(`/api/scenarios/${id}/solve`, { target, desired_legacy: desiredLegacy }),
};

export const projectAnonymous = (
  inputs: ScenarioInputs,
  dependents: Dependent[] = [],
  goals: Goal[] = [],
  income_streams: IncomeStream[] = []
) => api.post<ProjectionResult>("/api/project/anonymous", { inputs, dependents, goals, income_streams });
