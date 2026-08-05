import { Search } from "lucide-react";
import type { ScanListQuery, ScanStatus, ScanType } from "@/shared/types/scan";

export interface ScanFiltersState {
  search: string;
  status: ScanStatus | "";
  scan_type: ScanType | "";
}

interface ScanFiltersProps {
  filters: ScanFiltersState;
  onChange: (filters: ScanFiltersState) => void;
}

export function filtersToQuery(filters: ScanFiltersState, page: number, limit: number): ScanListQuery {
  return {
    page,
    limit,
    search: filters.search.trim() || undefined,
    status: filters.status || undefined,
    scan_type: filters.scan_type || undefined,
  };
}

export default function ScanFilters({ filters, onChange }: ScanFiltersProps) {
  const set = <K extends keyof ScanFiltersState>(key: K, value: ScanFiltersState[K]) =>
    onChange({ ...filters, [key]: value });

  return (
    <div className="space-y-3">
      <div className="relative">
        <Search
          size={16}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-brand-500"
        />
        <input
          value={filters.search}
          onChange={(e) => set("search", e.target.value)}
          className="input-field pl-9"
          placeholder="Search by profile or status..."
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <select
          value={filters.status}
          onChange={(e) => set("status", e.target.value as ScanStatus | "")}
          className="input-field"
          aria-label="Filter by status"
        >
          <option value="">All statuses</option>
          <option value="completed">Completed</option>
          <option value="running">Running</option>
          <option value="queued">Queued</option>
          <option value="pending">Pending</option>
          <option value="failed">Failed</option>
          <option value="cancelled">Cancelled</option>
        </select>

        <select
          value={filters.scan_type}
          onChange={(e) => set("scan_type", e.target.value as ScanType | "")}
          className="input-field"
          aria-label="Filter by profile"
        >
          <option value="">All profiles</option>
          <option value="quick">Quick Scan</option>
          <option value="full">Full Scan</option>
          <option value="custom">Custom Scan</option>
        </select>
      </div>
    </div>
  );
}
