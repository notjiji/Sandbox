import { useEffect, useState } from "react";
import { Clock } from "lucide-react";
import ActivityTimeline from "@/shared/components/activity/ActivityTimeline";
import FormAlert from "@/shared/components/FormAlert";
import { ApiError } from "@/shared/api/client";
import type { ActivityEvent } from "@/shared/types/activity";
import { SectionPanel } from "@/features/organizations/components/dashboard/StatCard";
import { assetsApi } from "../api";

interface AssetTimelinePanelProps {
  projectId: string;
  assetId: string;
}

export default function AssetTimelinePanel({ projectId, assetId }: AssetTimelinePanelProps) {
  const [items, setItems] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    assetsApi
      .timeline(projectId, assetId)
      .then((response) => {
        if (active) setItems(response?.items ?? []);
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof ApiError ? err.message : "Unable to load timeline.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [projectId, assetId]);

  return (
    <SectionPanel title="Timeline">
      {error && <FormAlert message={error} />}
      {loading ? (
        <p className="text-sm text-brand-600">Loading timeline...</p>
      ) : (
        <ActivityTimeline
          items={items}
          emptyMessage="Activity for this asset will appear here — scans, reports, risk changes, and updates."
        />
      )}
      {!loading && items.length > 0 && (
        <p className="mt-4 flex items-center gap-2 text-xs text-brand-600">
          <Clock size={14} />
          Monitoring events (DNS, certificates, ports) will appear here in a future release.
        </p>
      )}
    </SectionPanel>
  );
}
