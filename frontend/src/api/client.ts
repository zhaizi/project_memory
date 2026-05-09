import type { MemoryItem, SearchResult, Stats, ProjectInfo } from "../types";

const BASE = "/api";

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  listProjects(): Promise<ProjectInfo[]> {
    return request("/projects");
  },

  getStats(project: string): Promise<Stats> {
    return request(`/stats?project=${encodeURIComponent(project)}`);
  },

  listMemories(
    project: string,
    params?: { type?: string; limit?: number; offset?: number }
  ): Promise<MemoryItem[]> {
    const sp = new URLSearchParams({ project });
    if (params?.type) sp.set("type", params.type);
    if (params?.limit) sp.set("limit", String(params.limit));
    if (params?.offset) sp.set("offset", String(params.offset));
    return request(`/memories?${sp}`);
  },

  getMemory(id: number, project: string): Promise<MemoryItem> {
    return request(`/memories/${id}?project=${encodeURIComponent(project)}`);
  },

  createMemory(data: {
    content: string;
    memory_type: string;
    tags: string[];
    importance: number;
    project_path: string;
  }): Promise<MemoryItem> {
    return request("/memories", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },

  updateMemory(
    id: number,
    project: string,
    data: {
      content?: string;
      memory_type?: string;
      tags?: string[];
      importance?: number;
    }
  ): Promise<MemoryItem> {
    return request(`/memories/${id}?project=${encodeURIComponent(project)}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  },

  deleteMemory(id: number, project: string): Promise<{ success: boolean }> {
    return request(
      `/memories/${id}?project=${encodeURIComponent(project)}`,
      { method: "DELETE" }
    );
  },

  searchMemories(
    query: string,
    project: string,
    limit = 10
  ): Promise<SearchResult[]> {
    return request("/memories/search", {
      method: "POST",
      body: JSON.stringify({ query, project, limit }),
    });
  },
};
