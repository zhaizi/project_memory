import { useState, useEffect, useRef } from "react";
import type { MemoryItem } from "../types";
import { MEMORY_TYPES, MEMORY_TYPE_LABELS } from "../types";
import { api } from "../api/client";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  onSaved: () => void;
  memory?: MemoryItem | null;
  projectPath: string;
}

const TYPE_COLORS: Record<string, string> = {
  project_context: "text-blue-600 dark:text-blue-400",
  user_preference: "text-purple-600 dark:text-purple-400",
  bug_fix: "text-red-600 dark:text-red-400",
  code_pattern: "text-green-600 dark:text-green-400",
  decision: "text-amber-600 dark:text-amber-400",
  task_status: "text-cyan-600 dark:text-cyan-400",
};

function TypeDropdown({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const selected = MEMORY_TYPES.find((t) => t === value);

  return (
    <div ref={ref} className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={`w-full flex items-center justify-between px-3 py-2 rounded-lg
          bg-zinc-100 border border-zinc-200 text-sm
          dark:bg-white/5 dark:border-white/10
          focus:outline-none focus:ring-2 focus:ring-blue-500/50 cursor-pointer transition-colors`}
      >
        <span className={`inline-flex items-center gap-1.5 ${TYPE_COLORS[value] ?? ""}`}>
          <span className="w-2 h-2 rounded-full bg-current opacity-60" />
          {selected ? MEMORY_TYPE_LABELS[selected] : "选择类型"}
        </span>
        <svg className={`w-3.5 h-3.5 text-zinc-400 dark:text-white/40 transition-transform ${open ? "rotate-180" : ""}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">

          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && (
        <div className="absolute left-0 right-0 mt-1 rounded-lg bg-white border border-zinc-200 shadow-xl z-50 overflow-hidden dark:bg-zinc-900 dark:border-white/10">
          {MEMORY_TYPES.map((type) => (
            <button
              key={type}
              type="button"
              onClick={() => { onChange(type); setOpen(false); }}
              className={`w-full flex items-center gap-2 px-3 py-2 text-sm transition-colors cursor-pointer
                ${type === value ? "bg-blue-500/10 text-blue-500 dark:text-blue-300" : "text-zinc-600 hover:bg-zinc-50 dark:text-white/70 dark:hover:bg-white/5"}`}
            >
              <span className={`w-2 h-2 rounded-full ${TYPE_COLORS[type]?.split(" ")[0] ?? "bg-zinc-500"}`} />
              <span className="flex-1 text-left">{MEMORY_TYPE_LABELS[type]}</span>
              {type === value && (
                <svg className="w-4 h-4 text-blue-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
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

export default function MemoryEditor({ isOpen, onClose, onSaved, memory, projectPath }: Props) {
  const isEdit = !!memory;
  const [content, setContent] = useState("");
  const [memoryType, setMemoryType] = useState("project_context");
  const [importance, setImportance] = useState(5);
  const [tagsInput, setTagsInput] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (memory) {
      setContent(memory.content);
      setMemoryType(memory.memory_type);
      setImportance(memory.importance);
      setTagsInput(memory.tags.join(", "));
    } else {
      setContent("");
      setMemoryType("project_context");
      setImportance(5);
      setTagsInput("");
    }
    setError("");
  }, [memory, isOpen]);

  const handleSave = async () => {
    if (!content.trim()) { setError("内容不能为空"); return; }
    setSaving(true);
    setError("");
    const tags = tagsInput.split(",").map((t) => t.trim()).filter(Boolean);
    try {
      if (isEdit && memory) {
        await api.updateMemory(memory.id, projectPath, { content, memory_type: memoryType, tags, importance });
      } else {
        await api.createMemory({ content, memory_type: memoryType, tags, importance, project_path: projectPath });
      }
      onSaved();
      onClose();
    } catch (err) {
      setError(err instanceof Error ? err.message : "保存失败");
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      <div className="absolute inset-0 bg-black/60 backdrop-blur-sm dark:bg-black/60" onClick={onClose} />
      <div className="relative w-full max-w-lg rounded-2xl border border-zinc-300 bg-white shadow-2xl dark:border-white/10 dark:bg-zinc-900">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-zinc-200 dark:border-white/5">
          <h2 className="text-lg font-semibold text-zinc-900 dark:text-white">{isEdit ? `编辑记忆 #${memory?.id}` : "新建记忆"}</h2>
          <button onClick={onClose} className="w-8 h-8 rounded-lg hover:bg-zinc-100 dark:hover:bg-white/5 flex items-center justify-center text-zinc-400 hover:text-zinc-600 dark:text-white/40 dark:hover:text-white transition-colors cursor-pointer">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-4 space-y-4">
          <div>
            <label className="text-xs text-zinc-500 dark:text-white/30 mb-1.5 block">类型</label>
            <TypeDropdown value={memoryType} onChange={setMemoryType} />
          </div>
          <div>
            <label className="text-xs text-zinc-500 dark:text-white/30 mb-1.5 block">内容</label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              placeholder="输入记忆内容..."
              rows={4}
              className="w-full px-3 py-2 rounded-lg bg-zinc-100 border border-zinc-200 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 resize-none dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-white/15"
            />
          </div>
          <div>
            <label className="text-xs text-zinc-500 dark:text-white/30 mb-1.5 block">标签（逗号分隔）</label>
            <input
              type="text"
              value={tagsInput}
              onChange={(e) => setTagsInput(e.target.value)}
              placeholder="tag1, tag2, tag3"
              className="w-full px-3 py-2 rounded-lg bg-zinc-100 border border-zinc-200 text-sm text-zinc-900 placeholder:text-zinc-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-white/15"
            />
            {tagsInput && (
              <div className="flex gap-1 mt-2 flex-wrap">
                {tagsInput.split(",").map((t) => t.trim()).filter(Boolean).map((tag, i) => (
                  <span key={i} className="px-2 py-0.5 rounded-md bg-zinc-100 text-zinc-500 text-xs dark:bg-white/5 dark:text-white/40">{tag}</span>
                ))}
              </div>
            )}
          </div>
          <div>
            <label className="text-xs text-zinc-500 dark:text-white/30 mb-1.5 block">重要性: {importance}</label>
            <input
              type="range" min={1} max={10} step={1} value={importance}
              onChange={(e) => setImportance(Number(e.target.value))}
              className="w-full accent-blue-500"
            />
            <div className="flex justify-between text-[10px] text-zinc-400 dark:text-white/15 mt-1"><span>1</span><span>5</span><span>10</span></div>
          </div>
          {error && <p className="text-red-500 dark:text-red-400 text-sm">{error}</p>}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 px-6 py-4 border-t border-zinc-200 dark:border-white/5">
          <button onClick={onClose} className="px-4 py-2 rounded-xl text-sm text-zinc-500 hover:text-zinc-700 hover:bg-zinc-100 dark:text-white/40 dark:hover:text-white dark:hover:bg-white/5 transition-colors cursor-pointer">取消</button>
          <button onClick={handleSave} disabled={saving} className="px-4 py-2 rounded-xl bg-blue-500 text-white text-sm font-medium hover:bg-blue-600 disabled:opacity-40 cursor-pointer transition-colors dark:bg-blue-600 dark:hover:bg-blue-700">
            {saving ? "保存中..." : "保存"}
          </button>
        </div>
      </div>
    </div>
  );
}
