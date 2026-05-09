export interface MemoryItem {
  id: number;
  content: string;
  memory_type: string;
  tags: string[];
  project_path: string;
  importance: number;
  created_at: number;
  updated_at: number;
  access_count: number;
  last_accessed_at: number | null;
}

export interface SearchResult {
  memory: MemoryItem;
  score: number;
}

export interface Stats {
  total: number;
  by_type: Record<string, number>;
  project: string;
}

export interface ProjectInfo {
  path: string;
  name: string;
  memory_count: number;
}

export const MEMORY_TYPES = [
  "project_context",
  "user_preference",
  "bug_fix",
  "code_pattern",
  "decision",
  "task_status",
] as const;

export const MEMORY_TYPE_LABELS: Record<string, string> = {
  project_context: "项目上下文",
  user_preference: "用户偏好",
  bug_fix: "问题记录",
  code_pattern: "代码模式",
  decision: "决策记录",
  task_status: "任务状态",
};

export const MEMORY_TYPE_COLORS: Record<string, string> = {
  project_context: "primary",
  user_preference: "secondary",
  bug_fix: "danger",
  code_pattern: "success",
  decision: "warning",
  task_status: "default",
};
