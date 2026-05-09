import useSWR from "swr";
import { api } from "../api/client";
import type { Stats, MemoryItem, ProjectInfo } from "../types";

export function useProjects() {
  return useSWR<ProjectInfo[]>("/api/projects", () => api.listProjects());
}

export function useStats(project: string | null) {
  return useSWR<Stats>(
    project ? `/api/stats?project=${project}` : null,
    () => (project ? api.getStats(project) : Promise.reject("no project"))
  );
}

export function useMemories(
  project: string | null,
  params?: { type?: string; limit?: number }
) {
  const key = project
    ? `/api/memories?project=${project}&type=${params?.type ?? ""}&limit=${params?.limit ?? 50}`
    : null;
  return useSWR<MemoryItem[]>(key, () =>
    project ? api.listMemories(project, params) : Promise.reject("no project")
  );
}
