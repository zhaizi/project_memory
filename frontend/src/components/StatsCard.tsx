import type { Stats } from "../types";

interface Props {
  stats: Stats | undefined;
  isLoading: boolean;
}

export default function StatsCards({ stats, isLoading }: Props) {
  const cards = [
    { label: "总记忆数", value: stats?.total ?? 0, icon: "M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10", color: "text-blue-500 dark:text-blue-400" },
    { label: "类型分布", value: stats ? Object.keys(stats.by_type).length : 0, icon: "M11 3.055A9.001 9.001 0 10200.5 9M11 3.055v9.9m0 0a9 9 0 019 9", color: "text-purple-500 dark:text-purple-400" },
    { label: "项目路径", value: stats?.project ? stats.project.split(/[\\/]/).pop() ?? "-" : "-", icon: "M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z", color: "text-amber-500 dark:text-amber-400" },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
      {cards.map((card) => (
        <div key={card.label} className="rounded-xl border border-zinc-200 bg-white p-4 dark:border-white/5 dark:bg-white/[0.02] dark:backdrop-blur-sm">
          <div className="flex items-center gap-3">
            <div className={`w-8 h-8 rounded-lg bg-zinc-50 flex items-center justify-center dark:bg-white/5 ${card.color}`}>
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d={card.icon} />
              </svg>
            </div>
            <div>
              <p className="text-xs text-zinc-400 dark:text-white/25">{card.label}</p>
              <p className={`text-lg font-semibold ${card.color}`}>{isLoading ? "..." : card.value}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
