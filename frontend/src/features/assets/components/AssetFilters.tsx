import { Search } from "lucide-react";
import {
  ASSET_CATEGORIES,
  ASSET_CATEGORY_LABELS,
  ASSET_CRITICALITIES,
  ASSET_CRITICALITY_LABELS,
  ASSET_ENVIRONMENTS,
  ASSET_ENVIRONMENT_LABELS,
  ASSET_STATUSES,
  ASSET_STATUS_LABELS,
  ASSET_TYPE_GROUPS,
  ASSET_TYPE_LABELS,
} from "../types";
import type { AssetFiltersState } from "../utils/hierarchy";

interface AssetFiltersProps {
  filters: AssetFiltersState;
  onChange: (filters: AssetFiltersState) => void;
}

export default function AssetFilters({ filters, onChange }: AssetFiltersProps) {
  const set = (key: keyof AssetFiltersState, value: string) =>
    onChange({ ...filters, [key]: value });

  return (
    <div className="glass-panel space-y-4 p-4">
      <div className="relative">
        <Search
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-500"
        />
        <input
          value={filters.search}
          onChange={(e) => set("search", e.target.value)}
          className="input-field pl-9"
          placeholder="Search name, identifier, owner, business unit, tags..."
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">
        <select
          value={filters.type}
          onChange={(e) => set("type", e.target.value)}
          className="input-field"
          aria-label="Filter by type"
        >
          <option value="">All types</option>
          {ASSET_TYPE_GROUPS.map((group) => (
            <optgroup key={group.label} label={group.label}>
              {group.types.map((type) => (
                <option key={type} value={type}>
                  {ASSET_TYPE_LABELS[type]}
                </option>
              ))}
            </optgroup>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(e) => set("status", e.target.value)}
          className="input-field"
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          {ASSET_STATUSES.map((status) => (
            <option key={status} value={status}>
              {ASSET_STATUS_LABELS[status]}
            </option>
          ))}
        </select>

        <select
          value={filters.environment}
          onChange={(e) => set("environment", e.target.value)}
          className="input-field"
          aria-label="Filter by environment"
        >
          <option value="">All environments</option>
          {ASSET_ENVIRONMENTS.map((environment) => (
            <option key={environment} value={environment}>
              {ASSET_ENVIRONMENT_LABELS[environment]}
            </option>
          ))}
        </select>

        <select
          value={filters.criticality}
          onChange={(e) => set("criticality", e.target.value)}
          className="input-field"
          aria-label="Filter by criticality"
        >
          <option value="">All criticalities</option>
          {ASSET_CRITICALITIES.map((criticality) => (
            <option key={criticality} value={criticality}>
              {ASSET_CRITICALITY_LABELS[criticality]}
            </option>
          ))}
        </select>

        <select
          value={filters.asset_category}
          onChange={(e) => set("asset_category", e.target.value)}
          className="input-field"
          aria-label="Filter by category"
        >
          <option value="">All categories</option>
          {ASSET_CATEGORIES.map((category) => (
            <option key={category} value={category}>
              {ASSET_CATEGORY_LABELS[category]}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}
