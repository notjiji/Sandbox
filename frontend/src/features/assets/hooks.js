import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/shared/api/client";
import { assetsApi } from "./api";

export function useProjectAssets(projectId) {
  const [assets, setAssets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await assetsApi.list(projectId);
      setAssets(response?.data?.items ?? []);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unable to load assets.");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { assets, loading, error, reload };
}
