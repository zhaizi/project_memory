import { useState } from "react";
import type { SearchResult } from "../types";
import { api } from "../api/client";

interface Props {
  projectPath: string;
  onResults: (results: SearchResult[]) => void;
}

export default function SearchBar({ projectPath, onResults }: Props) {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setSearching(true);
    try {
      const results = await api.searchMemories(query, projectPath);
      onResults(results);
    } catch {
      onResults([]);
    } finally {
      setSearching(false);
    }
  };

  return (
    <div className="flex gap-2">
      <div className="flex-1 relative">
        <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-300 dark:text-white/20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter") handleSearch(); }}
          placeholder="语义搜索记忆..."
          className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-white border border-zinc-200 text-sm text-zinc-900
                     placeholder:text-zinc-300 focus:outline-none focus:ring-2 focus:ring-blue-500/30 focus:border-blue-500
                     dark:bg-white/5 dark:border-white/10 dark:text-white dark:placeholder:text-white/20
                     dark:focus:ring-primary/20 dark:focus:border-primary/50 transition-all"
        />
      </div>
      <button
        onClick={handleSearch}
        disabled={searching}
        className="px-5 py-2.5 rounded-xl bg-blue-500 text-white text-sm font-medium
                   hover:bg-blue-600 disabled:opacity-40 cursor-pointer transition-colors
                   dark:bg-primary dark:hover:bg-primary/90"
      >
        {searching ? "搜索中..." : "搜索"}
      </button>
    </div>
  );
}
