import { Search } from "lucide-react";
import type { MemberFiltersState } from "@/shared/types/member";
import type { OrganizationRole } from "@/shared/types/organization";
import type { RoleInfo } from "@/shared/types/member";

interface MemberFiltersProps {
  filters: MemberFiltersState;
  roles: RoleInfo[];
  onChange: (filters: MemberFiltersState) => void;
}

const STATUS_OPTIONS = [
  { value: "", label: "All statuses" },
  { value: "active", label: "Active" },
  { value: "pending", label: "Pending" },
  { value: "suspended", label: "Suspended" },
] as const;

const SORT_OPTIONS = [
  { value: "name", label: "Name" },
  { value: "email", label: "Email" },
  { value: "role", label: "Role" },
  { value: "status", label: "Status" },
  { value: "joined_at", label: "Joined" },
  { value: "last_login", label: "Last login" },
] as const;

export default function MemberFilters({ filters, roles, onChange }: MemberFiltersProps) {
  const set = <K extends keyof MemberFiltersState>(key: K, value: MemberFiltersState[K]) =>
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
          placeholder="Search by name or email..."
          aria-label="Search members"
        />
      </div>

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <select
          value={filters.status}
          onChange={(e) => set("status", e.target.value as MemberFiltersState["status"])}
          className="input-field"
          aria-label="Filter by status"
        >
          {STATUS_OPTIONS.map((option) => (
            <option key={option.value || "all"} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <select
          value={filters.role}
          onChange={(e) => set("role", e.target.value as OrganizationRole | "")}
          className="input-field"
          aria-label="Filter by role"
        >
          <option value="">All roles</option>
          {roles.map((role) => (
            <option key={role.role} value={role.role}>
              {role.role.replace(/_/g, " ")}
            </option>
          ))}
        </select>

        <select
          value={filters.sort}
          onChange={(e) => set("sort", e.target.value as MemberFiltersState["sort"])}
          className="input-field"
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
          onChange={(e) => set("order", e.target.value as MemberFiltersState["order"])}
          className="input-field"
          aria-label="Sort order"
        >
          <option value="asc">Ascending</option>
          <option value="desc">Descending</option>
        </select>
      </div>
    </div>
  );
}
