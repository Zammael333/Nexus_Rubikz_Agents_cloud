"use client";

import { useState, useCallback } from "react";

interface FilterOption {
  key: string;
  label: string;
  values: string[];
}

interface SearchFilterProps {
  placeholder?: string;
  filters: FilterOption[];
  onSearch: (query: string, activeFilters: Record<string, string>) => void;
}

export default function SearchFilter({ placeholder = "Search...", filters, onSearch }: SearchFilterProps) {
  const [query, setQuery] = useState("");
  const [activeFilters, setActiveFilters] = useState<Record<string, string>>({});
  const [expanded, setExpanded] = useState(false);

  const handleSearch = useCallback(() => {
    onSearch(query, activeFilters);
  }, [query, activeFilters, onSearch]);

  return (
    <div className="bg-nexus-surface border border-nexus-border rounded-lg">
      <div className="flex items-center gap-2 p-2">
        <span className="text-nexus-muted text-sm">🔍</span>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          placeholder={placeholder}
          className="flex-1 bg-transparent text-xs text-nexus-text placeholder-nexus-muted outline-none border-none font-mono"
        />
        <button
          onClick={() => setExpanded(!expanded)}
          className="text-[10px] text-nexus-muted hover:text-nexus-text uppercase tracking-wider"
        >
          {expanded ? "Hide" : "Filters"}
        </button>
        <button
          onClick={handleSearch}
          className="px-3 py-1 bg-edge-green/20 text-edge-green text-[10px] uppercase tracking-wider rounded hover:bg-edge-green/30 transition-colors"
        >
          Search
        </button>
      </div>
      {expanded && (
        <div className="border-t border-nexus-border p-3 grid grid-cols-2 md:grid-cols-4 gap-3">
          {filters.map((f) => (
            <div key={f.key}>
              <label className="text-[10px] text-nexus-muted uppercase tracking-wider block mb-1">{f.label}</label>
              <select
                value={activeFilters[f.key] || ""}
                onChange={(e) => setActiveFilters((prev) => ({ ...prev, [f.key]: e.target.value }))}
                className="w-full bg-nexus-bg border border-nexus-border rounded px-2 py-1 text-xs text-nexus-text font-mono outline-none"
              >
                <option value="">All</option>
                {f.values.map((v) => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
