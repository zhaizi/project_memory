import type { MemoryItem } from "../types";
import { MEMORY_TYPE_LABELS } from "../types";

interface Props {
  memories: MemoryItem[];
  isLoading: boolean;
  onSelect: (memory: MemoryItem) => void;
  onDelete: (id: number) => void;
}

function timeAgo(ts: number): string {
  const diff = Date.now() / 1000 - ts;
  if (diff < 60) return "刚刚";
  if (diff < 3600) return `${Math.floor(diff / 60)}分钟前`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}小时前`;
  return `${Math.floor(diff / 86400)}天前`;
}

const TYPE_COLORS: Record<string, string> = {
  project_context: "bg-blue-500/10 text-blue-500 dark:bg-blue-500/10 dark:text-blue-400",
  user_preference: "bg-purple-500/10 text-purple-500 dark:bg-purple-500/10 dark:text-purple-400",
  bug_fix: "bg-red-500/10 text-red-500 dark:bg-red-500/10 dark:text-red-400",
  code_pattern: "bg-green-500/10 text-green-500 dark:bg-green-500/10 dark:text-green-400",
  decision: "bg-amber-500/10 text-amber-500 dark:bg-amber-500/10 dark:text-amber-400",
  task_status: "bg-cyan-500/10 text-cyan-500 dark:bg-cyan-500/10 dark:text-cyan-400",
};

export default function MemoryTable({ memories, isLoading, onSelect, onDelete }: Props) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12 text-zinc-400 dark:text-white/30">
        <svg className="animate-spin w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
        加载中...
      </div>
    );
  }

  if (memories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-zinc-300 dark:text-white/20">
        <svg className="w-12 h-12 mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
        </svg>
        <p>暂无记忆数据</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl border border-zinc-200 bg-white overflow-hidden dark:border-white/5 dark:bg-transparent">
      <table className="w-full text-sm">
        <thead>
          <tr className="bg-zinc-50 border-b border-zinc-200 dark:bg-white/[0.02] dark:border-white/5">
            <th className="px-4 py-3 text-left text-zinc-400 font-medium w-16 dark:text-white/30">ID</th>
            <th className="px-4 py-3 text-left text-zinc-400 font-medium w-28 dark:text-white/30">类型</th>
            <th className="px-4 py-3 text-left text-zinc-400 font-medium w-20 dark:text-white/30">重要性</th>
            <th className="px-4 py-3 text-left text-zinc-400 font-medium dark:text-white/30">内容</th>
            <th className="px-4 py-3 text-left text-zinc-400 font-medium w-36 dark:text-white/30">标签</th>
            <th className="px-4 py-3 text-left text-zinc-400 font-medium w-24 dark:text-white/30">时间</th>
            <th className="px-4 py-3 text-left text-zinc-400 font-medium w-28 dark:text-white/30">操作</th>
          </tr>
        </thead>
        <tbody>
          {memories.map((item) => (
            <tr key={item.id} className="border-b border-zinc-100 hover:bg-zinc-50 transition-colors dark:border-white/[0.03] dark:hover:bg-white/[0.02]">
              <td className="px-4 py-3 text-zinc-400 dark:text-white/30">#{item.id}</td>
              <td className="px-4 py-3">
                <span className={`inline-block px-2 py-0.5 rounded-md text-xs ${TYPE_COLORS[item.memory_type] ?? "bg-zinc-100 text-zinc-500 dark:bg-white/5 dark:text-white/40"}`}>
                  {MEMORY_TYPE_LABELS[item.memory_type] ?? item.memory_type}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className={
                  item.importance >= 8 ? "text-red-500 font-bold dark:text-red-400" :
                  item.importance >= 5 ? "text-amber-500 dark:text-amber-400" : "text-zinc-300 dark:text-white/30"
                }>
                  {item.importance}
                </span>
              </td>
              <td className="px-4 py-3">
                <span className="line-clamp-1 max-w-[320px] block text-zinc-600 dark:text-white/60">
                  {item.content.slice(0, 80)}{item.content.length > 80 ? "..." : ""}
                </span>
              </td>
              <td className="px-4 py-3">
                <div className="flex gap-1 flex-wrap">
                  {item.tags.slice(0, 3).map((tag) => (
                    <span key={tag} className="px-1.5 py-0.5 rounded bg-zinc-100 text-zinc-400 text-xs dark:bg-white/5 dark:text-white/30">{tag}</span>
                  ))}
                </div>
              </td>
              <td className="px-4 py-3 text-zinc-400 text-xs dark:text-white/25">{timeAgo(item.updated_at)}</td>
              <td className="px-4 py-3">
                <div className="flex gap-2">
                  <button onClick={() => onSelect(item)} className="text-blue-500 hover:text-blue-600 text-xs cursor-pointer transition-colors dark:text-blue-400 dark:hover:text-blue-300">编辑</button>
                  <button onClick={() => onDelete(item.id)} className="text-red-500 hover:text-red-600 text-xs cursor-pointer transition-colors dark:text-red-400 dark:hover:text-red-300">删除</button>
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
