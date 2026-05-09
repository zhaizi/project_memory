import { useState, useCallback, useRef, useEffect } from "react";
import StatsCards from "./components/StatsCard";
import MemoryTable from "./components/MemoryTable";
import MemoryEditor from "./components/MemoryEditor";
import SearchBar from "./components/SearchBar";
import ThemeToggle, { useTheme } from "./components/ThemeToggle";
import { useProjects, useStats, useMemories } from "./hooks/useMemories";
import { api } from "./api/client";
import type { MemoryItem, SearchResult } from "./types";
import { MEMORY_TYPE_LABELS } from "./types";

/* ---------- 现代风格下拉框 ---------- */
function ModernDropdown({
  options,
  value,
  onChange,
  placeholder,
}: {
  options: { key: string; label: string; badge?: string }[];
  value: string | null;
  onChange: (key: string | null) => void;
  placeholder: string;
}) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const selected = options.find((o) => o.key === value);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-4 py-2 rounded-xl
          bg-zinc-100 border border-zinc-200 hover:bg-zinc-150
          dark:bg-white/5 dark:border-white/10 dark:hover:bg-white/10
          transition-all text-sm cursor-pointer backdrop-blur-sm text-zinc-700 dark:text-white"
      >
        <svg className="w-4 h-4 text-zinc-400 dark:text-white/40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
        </svg>
        <span>{selected?.label ?? placeholder}</span>
        {selected?.badge && (
          <span className="px-1.5 py-0.5 rounded-full bg-blue-500/10 text-blue-500 text-xs dark:bg-primary/20 dark:text-primary">{selected.badge}</span>
        )}
        <svg className={`w-3.5 h-3.5 text-zinc-400 dark:text-white/40 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="absolute right-0 mt-2 w-64 rounded-xl bg-white border border-zinc-200 shadow-xl z-50 overflow-hidden dark:bg-zinc-900 dark:border-white/10 dark:backdrop-blur-xl">
          {options.map((opt) => (
            <button
              key={opt.key}
              onClick={() => { onChange(opt.key === value ? null : opt.key); setOpen(false); }}
              className={`w-full flex items-center gap-2 px-4 py-2.5 text-sm transition-colors cursor-pointer
                ${opt.key === value
                  ? "bg-blue-500/10 text-blue-500 dark:bg-primary/10 dark:text-primary"
                  : "text-zinc-600 hover:bg-zinc-50 dark:text-white dark:hover:bg-white/5"}`}
            >
              <span className="flex-1 text-left">{opt.label}</span>
              {opt.badge && <span className="px-1.5 py-0.5 rounded-full bg-zinc-100 text-zinc-500 text-xs dark:bg-white/10 dark:text-white/50">{opt.badge}</span>}
              {opt.key === value && (
                <svg className="w-4 h-4 text-blue-500 dark:text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

/* ---------- 自定义 Tab ---------- */
function CustomTabs({ active, onChange, tabs }: {
  active: string;
  onChange: (id: string) => void;
  tabs: { id: string; label: string }[];
}) {
  return (
    <div className="flex gap-1 p-1 rounded-xl bg-zinc-100 border border-zinc-200 dark:bg-white/5 dark:border-white/5">
      {tabs.map((tab) => (
        <button
          key={tab.id}
          onClick={() => onChange(tab.id)}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-all cursor-pointer
            ${active === tab.id
              ? "bg-blue-500 text-white shadow-sm dark:bg-primary dark:text-primary-foreground"
              : "text-zinc-500 hover:text-zinc-700 hover:bg-zinc-50 dark:text-white/40 dark:hover:text-white dark:hover:bg-white/5"}`}
        >
          {tab.label}
        </button>
      ))}
    </div>
  );
}

/* ---------- 删除确认对话框 ---------- */
function DeleteDialog({ target, onClose, onConfirm }: {
  target: number | null;
  onClose: () => void;
  onConfirm: () => void;
}) {
  if (target === null) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm dark:bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-sm rounded-2xl border border-zinc-200 bg-white shadow-2xl dark:border-white/10 dark:bg-zinc-900">
        <div className="px-6 py-4 border-b border-zinc-100 dark:border-white/5">
          <h3 className="text-lg font-semibold text-zinc-900 dark:text-white">确认删除</h3>
        </div>
        <div className="px-6 py-4">
          <p className="text-zinc-500 dark:text-white/40">确定要删除这条记忆吗？此操作不可撤销。</p>
        </div>
        <div className="flex justify-end gap-2 px-6 py-4 border-t border-zinc-100 dark:border-white/5">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-zinc-500 hover:text-zinc-700 hover:bg-zinc-100 dark:text-white/40 dark:hover:text-white dark:hover:bg-white/5 transition-colors cursor-pointer">取消</button>
          <button onClick={onConfirm} className="px-4 py-2 rounded-xl bg-red-500 text-white text-sm font-medium hover:bg-red-600 transition-colors cursor-pointer">删除</button>
        </div>
      </div>
    </div>
  );
}

/* ---------- 主应用 ---------- */
export default function App() {
  const { dark, toggle: toggleTheme } = useTheme();
  const [selectedProject, setSelectedProject] = useState<string | null>(null);
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingMemory, setEditingMemory] = useState<MemoryItem | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<number | null>(null);
  const [searchResults, setSearchResults] = useState<SearchResult[] | null>(null);
  const [activeTab, setActiveTab] = useState("list");

  const { data: projects } = useProjects();
  const projectPath = selectedProject ?? "";

  const { data: stats, isLoading: statsLoading } = useStats(selectedProject);
  const { data: memories, isLoading: memoriesLoading, mutate } = useMemories(
    selectedProject,
    typeFilter ? { type: typeFilter } : undefined
  );

  const handleSelect = useCallback((memory: MemoryItem) => {
    setEditingMemory(memory);
    setEditorOpen(true);
  }, []);

  const handleDelete = useCallback(
    async (id: number) => {
      if (!selectedProject) return;
      try {
        await api.deleteMemory(id, selectedProject);
        mutate();
        setDeleteTarget(null);
      } catch (err) {
        alert(err instanceof Error ? err.message : "删除失败");
      }
    },
    [selectedProject, mutate]
  );

  const handleSearchResults = useCallback((results: SearchResult[]) => {
    setSearchResults(results);
    setActiveTab("search");
  }, []);

  const refresh = useCallback(() => {
    mutate();
    setSearchResults(null);
  }, [mutate]);

  const projectOptions = (projects ?? []).map((p) => ({
    key: p.path,
    label: p.name,
    badge: String(p.memory_count),
  }));

  const typeOptions = Object.entries(MEMORY_TYPE_LABELS).map(([key, label]) => ({ key, label }));

  return (
    <div className="min-h-screen bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-white transition-colors">
      {/* Header */}
      <header className="border-b border-zinc-200 px-6 py-4 backdrop-blur-sm bg-white/80 dark:border-white/5 dark:bg-zinc-950/80 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 flex items-center justify-center dark:bg-primary/20">
              <svg className="w-4 h-4 text-blue-500 dark:text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
              </svg>
            </div>
            <h1 className="text-lg font-semibold tracking-tight">Project Memory</h1>
          </div>
          <div className="flex items-center gap-3">
            <ThemeToggle dark={dark} toggle={toggleTheme} />
            <ModernDropdown options={projectOptions} value={selectedProject} onChange={setSelectedProject} placeholder="选择项目" />
            <button
              disabled={!selectedProject}
              onClick={() => { setEditingMemory(null); setEditorOpen(true); }}
              className="px-4 py-2 rounded-xl bg-blue-500 text-white text-sm font-medium
                         hover:bg-blue-600 disabled:opacity-40 disabled:cursor-not-allowed cursor-pointer
                         dark:bg-primary dark:hover:bg-primary/90 transition-colors"
            >
              + 新建记忆
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-6 space-y-6">
        {!selectedProject ? (
          <div className="flex flex-col items-center justify-center py-24">
            <div className="w-16 h-16 rounded-2xl bg-zinc-100 flex items-center justify-center mb-4 dark:bg-white/5">
              <svg className="w-8 h-8 text-zinc-300 dark:text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
              </svg>
            </div>
            <p className="text-lg font-medium text-zinc-400 dark:text-white/40">请选择一个项目开始</p>
            <p className="text-sm mt-1 text-zinc-300 dark:text-white/20">使用 project-memory CLI 保存记忆后，在此查看和管理</p>
          </div>
        ) : (
          <>
            <StatsCards stats={stats} isLoading={statsLoading} />

            <div className="flex items-center justify-between">
              <CustomTabs
                active={activeTab}
                onChange={(id) => { setActiveTab(id); if (id === "list") setSearchResults(null); }}
                tabs={[{ id: "list", label: "记忆列表" }, { id: "search", label: "语义搜索" }]}
              />
              {activeTab === "list" && (
                <div className="flex items-center gap-2">
                  <ModernDropdown options={typeOptions} value={typeFilter || null} onChange={(key) => setTypeFilter(key ?? "")} placeholder="全部类型" />
                  <button onClick={refresh} className="px-3 py-2 rounded-lg text-sm text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 dark:text-white/40 dark:hover:text-white dark:hover:bg-white/5 transition-colors cursor-pointer">刷新</button>
                </div>
              )}
            </div>

            {activeTab === "list" && (
              <MemoryTable memories={memories ?? []} isLoading={memoriesLoading} onSelect={handleSelect} onDelete={(id) => setDeleteTarget(id)} />
            )}

            {activeTab === "search" && (
              <div className="space-y-4">
                <SearchBar projectPath={projectPath} onResults={handleSearchResults} />
                {searchResults && searchResults.length > 0 && (
                  <div className="space-y-3">
                    {searchResults.map((r) => (
                      <div key={r.memory.id} className="rounded-xl border border-zinc-200 bg-white p-4 hover:bg-zinc-50 cursor-pointer transition-colors dark:border-white/5 dark:bg-transparent dark:hover:bg-white/5" onClick={() => handleSelect(r.memory)}>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-xs text-zinc-400 dark:text-white/40">#{r.memory.id}</span>
                          <span className="text-xs text-blue-500 dark:text-primary">{MEMORY_TYPE_LABELS[r.memory.memory_type] ?? r.memory.memory_type}</span>
                          <span className="text-xs text-green-500 dark:text-green-400">相似度: {(r.score * 100).toFixed(1)}%</span>
                        </div>
                        <p className="text-sm text-zinc-700 dark:text-white/80">{r.memory.content}</p>
                      </div>
                    ))}
                  </div>
                )}
                {searchResults && searchResults.length === 0 && (
                  <p className="text-center py-8 text-zinc-400 dark:text-white/40">未找到相关记忆</p>
                )}
              </div>
            )}
          </>
        )}
      </main>

      <MemoryEditor isOpen={editorOpen} onClose={() => setEditorOpen(false)} onSaved={refresh} memory={editingMemory} projectPath={projectPath} />
      <DeleteDialog target={deleteTarget} onClose={() => setDeleteTarget(null)} onConfirm={() => { if (deleteTarget !== null) handleDelete(deleteTarget); }} />
    </div>
  );
}
