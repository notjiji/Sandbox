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
import AssetTagFilters, { AssetSavedFiltersMenu } from "./AssetTagFilters";

interface AssetFiltersProps {
  projectId: string;
  filters: AssetFiltersState;
  onChange: (filters: AssetFiltersState) => void;
}

const SORT_OPTIONS: Array<{ value: AssetFiltersState["sort"]; label: string }> = [
  { value: "name", label: "Name" },
  { value: "created_at", label: "Created" },
  { value: "updated_at", label: "Updated" },
  { value: "criticality", label: "Criticality" },
  { value: "environment", label: "Environment" },
  { value: "type", label: "Type" },
];

export default function AssetFilters({ projectId, filters, onChange }: AssetFiltersProps) {
  const set = <K extends keyof AssetFiltersState>(key: K, value: AssetFiltersState[K]) =>
    onChange({ ...filters, [key]: value });

  return (
    <div className="glass-panel space-y-4 p-4">
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <div className="relative min-w-0 flex-1">
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
        <AssetSavedFiltersMenu projectId={projectId} filters={filters} onApply={onChange} />
      </div>

      <AssetTagFilters
        projectId={projectId}
        selectedTags={filters.tags}
        onChange={(tags) => set("tags", tags)}
      />

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
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

        <div className="flex gap-2">
          <select
            value={filters.sort}
            onChange={(e) => set("sort", e.target.value as AssetFiltersState["sort"])}
            className="input-field min-w-0 flex-1"
            aria-label="Sort by"
          >
            {SORT_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                Sort: {option.label}
              </option>
            ))}
          </select>
          <select
            value={filters.order}
            onChange={(e) => set("order", e.target.value as AssetFiltersState["order"])}
            className="input-field w-28"
            aria-label="Sort order"
          >
            <option value="asc">Asc</option>
            <option value="desc">Desc</option>
          </select>
        </div>
      </div>
    </div>
  );
}
