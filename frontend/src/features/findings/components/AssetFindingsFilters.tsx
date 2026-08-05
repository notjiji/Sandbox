import { Search } from "lucide-react";
import type { FindingListQuery, FindingSeverity } from "@/shared/types/finding";
import type { FindingSortField, FindingStatusGroup } from "../utils";
import { FINDING_SEVERITIES } from "../utils";

export interface AssetFindingsFiltersState {
  search: string;
  status_group: FindingStatusGroup;
  severity: FindingSeverity | "";
  sort: FindingSortField;
  order: "asc" | "desc";
}

interface AssetFindingsFiltersProps {
  filters: AssetFindingsFiltersState;
  onChange: (filters: AssetFindingsFiltersState) => void;
}

export function filtersToQuery(
  filters: AssetFindingsFiltersState,
  page: number,
  limit: number,
): FindingListQuery {
  return {
    page,
    limit,
    search: filters.search.trim() || undefined,
    status_group: filters.status_group || undefined,
    severity: filters.severity || undefined,
    sort: filters.sort,
    order: filters.order,
  };
}

const STATUS_TABS: { value: FindingStatusGroup; label: string }[] = [
  { value: "", label: "All" },
  { value: "open", label: "Open" },
  { value: "resolved", label: "Resolved" },
  { value: "ignored", label: "Ignored" },
];

export default function AssetFindingsFilters({
  filters,
  onChange,
}: AssetFindingsFiltersProps) {
  const set = <K extends keyof AssetFindingsFiltersState>(
    key: K,
    value: AssetFindingsFiltersState[K],
  ) => onChange({ ...filters, [key]: value });

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap gap-2">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value || "all"}
            type="button"
            onClick={() => set("status_group", tab.value)}
            className={`rounded-md border px-3 py-1.5 text-sm transition-colors ${
              filters.status_group === tab.value
                ? "border-brand-400 bg-brand-800/60 text-brand-100"
                : "border-brand-800/50 text-brand-400 hover:border-brand-700"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="grid gap-3 lg:grid-cols-[1fr_repeat(3,minmax(0,10rem))]">
        <div className="relative">
          <Search
            size={16}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-500"
          />
          <input
            value={filters.search}
            onChange={(e) => set("search", e.target.value)}
            className="input-field pl-9"
            placeholder="Search findings..."
          />
        </div>

        <select
          value={filters.severity}
          onChange={(e) => set("severity", e.target.value as FindingSeverity | "")}
          className="input-field"
          aria-label="Filter by severity"
        >
          <option value="">All severities</option>
          {FINDING_SEVERITIES.map((severity) => (
            <option key={severity} value={severity}>
              {severity.charAt(0).toUpperCase() + severity.slice(1)}
            </option>
          ))}
        </select>

        <select
          value={filters.sort}
          onChange={(e) => set("sort", e.target.value as FindingSortField)}
          className="input-field"
          aria-label="Sort findings"
        >
          <option value="risk_score">Sort by risk score</option>
          <option value="severity">Sort by severity</option>
          <option value="title">Sort by title</option>
          <option value="created_at">Sort by date</option>
        </select>

        <select
          value={filters.order}
          onChange={(e) => set("order", e.target.value as "asc" | "desc")}
          className="input-field"
          aria-label="Sort order"
        >
          <option value="desc">Highest first</option>
          <option value="asc">Lowest first</option>
        </select>
      </div>
    </div>
  );
}
