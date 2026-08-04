import { useEffect, useState } from "react";
import { membersApi } from "../api";
import { ApiError } from "@/shared/api/client";
import type { MemberFiltersState, MemberSummary } from "@/shared/types/member";
import { DEFAULT_MEMBER_FILTERS } from "@/shared/types/member";

interface UseOrganizationMembersOptions {
  page: number;
  limit: number;
  filters: MemberFiltersState;
  reloadToken?: number;
}

export function useOrganizationMembers({
  page,
  limit,
  filters,
  reloadToken = 0,
}: UseOrganizationMembersOptions) {
  const [members, setMembers] = useState<MemberSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(filters.search), 300);
    return () => window.clearTimeout(timer);
  }, [filters.search]);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      setError("");
      try {
        const response = await membersApi.listMembers({
          page,
          limit,
          search: debouncedSearch || undefined,
          status: filters.status || undefined,
          role: filters.role || undefined,
          sort: filters.sort,
          order: filters.order,
        });
        if (!active) return;
        setMembers(response?.items ?? []);
        setTotal(response?.total ?? 0);
      } catch (err) {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Unable to load members.");
          setMembers([]);
          setTotal(0);
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [page, limit, debouncedSearch, filters.status, filters.role, filters.sort, filters.order, reloadToken]);

  return { members, total, loading, error };
}

export { DEFAULT_MEMBER_FILTERS };
