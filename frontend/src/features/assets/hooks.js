import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError } from "@/shared/api/client";
import { assetsApi } from "./api";

function buildQuery(filters = {}) {
  const query = {
    page: filters.page ?? 1,
    limit: filters.limit ?? 50,
  };
  if (filters.search?.trim()) query.search = filters.search.trim();
  if (filters.type) query.type = filters.type;
  if (filters.status) query.status = filters.status;
  if (filters.environment) query.environment = filters.environment;
  if (filters.criticality) query.criticality = filters.criticality;
  return query;
}

export function useProjectAssets(projectId, filters = {}) {
  const [assets, setAssets] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [debouncedSearch, setDebouncedSearch] = useState(filters.search ?? "");

  useEffect(() => {
    const timer = setTimeout(() => setDebouncedSearch(filters.search ?? ""), 300);
    return () => clearTimeout(timer);
  }, [filters.search]);

  const query = useMemo(
    () => buildQuery({ ...filters, search: debouncedSearch }),
    [
      debouncedSearch,
      filters.type,
      filters.status,
      filters.environment,
      filters.criticality,
      filters.page,
      filters.limit,
    ],
  );

  const reload = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await assetsApi.list(projectId, query);
      setAssets(response?.data?.items ?? []);
      setTotal(response?.data?.total ?? 0);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load assets.");
    } finally {
      setLoading(false);
    }
  }, [projectId, query]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { assets, total, loading, error, reload };
}

export function useAsset(projectId, assetId) {
  const [asset, setAsset] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    if (!projectId || !assetId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await assetsApi.get(projectId, assetId);
      setAsset(response?.data ?? null);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load asset.");
    } finally {
      setLoading(false);
    }
  }, [projectId, assetId]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { asset, loading, error, reload };
}

export function useAssetAuditHistory(projectId, assetId) {
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let active = true;
    if (!projectId || !assetId) return undefined;

    setLoading(true);
    assetsApi.auditHistory(projectId, assetId)
      .then((response) => {
        if (active) setAuditLogs(response?.data?.items ?? []);
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
