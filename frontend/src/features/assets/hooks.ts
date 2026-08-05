import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError } from "@/shared/api/client";
import type { AssetListQuery, AssetSummary } from "@/shared/types/asset";
import { assetsApi } from "./api";

function buildQuery(filters: AssetListQuery = {}): AssetListQuery {
  const query: AssetListQuery = {
    page: filters.page ?? 1,
    limit: filters.limit ?? 50,
  };
  if (filters.search?.trim()) query.search = filters.search.trim();
  if (filters.tags?.length) query.tags = filters.tags;
  if (filters.type) query.type = filters.type;
  if (filters.status) query.status = filters.status;
  if (filters.environment) query.environment = filters.environment;
  if (filters.criticality) query.criticality = filters.criticality;
  if (filters.asset_category) query.asset_category = filters.asset_category;
  if (filters.sort) query.sort = filters.sort;
  if (filters.order) query.order = filters.order;
  if (filters.roots_only) query.roots_only = true;
  return query;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  details?: Record<string, unknown>;
  created_at: string;
}

export function useProjectAssets(projectId: string | undefined, filters: AssetListQuery = {}) {
  const [assets, setAssets] = useState<AssetSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search ?? "");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(filters.search ?? ""), 300);
    return () => clearTimeout(timer);
  }, [filters.search]);

  const query = useMemo(
    () => buildQuery({ ...filters, search: debouncedSearch }),
    [
      debouncedSearch,
      filters.tags,
      filters.type,
      filters.status,
      filters.environment,
      filters.criticality,
      filters.asset_category,
      filters.sort,
      filters.order,
      filters.page,
      filters.limit,
      filters.roots_only,
    ],
  );

  const reload = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await assetsApi.list(projectId, query);
      setAssets(response?.items ?? []);
      setTotal(response?.total ?? 0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load assets.");
    } finally {
      setLoading(false);
    }
  }, [projectId, query]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { assets, total, loading, error, reload };
}

export function useAsset(projectId: string | undefined, assetId: string | undefined) {
  const [asset, setAsset] = useState<AssetSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    if (!projectId || !assetId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await assetsApi.get(projectId, assetId);
      setAsset(response ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load asset.");
    } finally {
      setLoading(false);
    }
  }, [projectId, assetId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  return { asset, loading, error, reload };
}

export function useAssetAuditHistory(projectId: string | undefined, assetId: string | undefined) {
  const [auditLogs, setAuditLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    if (!projectId || !assetId) return undefined;

    setLoading(true);
    assetsApi
      .auditHistory(projectId, assetId)
      .then((response) => {
        if (active) {
          const items = (response as { items?: AuditLogEntry[] } | undefined)?.items ?? [];
          setAuditLogs(items);
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Unable to load audit history.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, [projectId, assetId]);

  return { auditLogs, loading, error };
}
