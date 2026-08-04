import { useEffect, useMemo, useState } from "react";
import { useParams } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import Pagination from "@/shared/components/Pagination";
import ActivityTimeline from "@/shared/components/activity/ActivityTimeline";
import EmptyState from "@/shared/components/EmptyState";
import ListSearchBar from "@/shared/components/ListSearchBar";
import { ListSkeleton } from "@/shared/components/ui/Skeleton";
import { toast } from "@/shared/lib/toast";
import { ApiError } from "@/shared/api/client";
import type { ActivityEvent } from "@/shared/types/activity";
import { organizationsApi } from "../api";

const PAGE_SIZE = 20;

export default function OrganizationActivity() {
  const [items, setItems] = useState<ActivityEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;

    async function load() {
      setLoading(true);
      try {
        const data = await organizationsApi.getActivity(page, PAGE_SIZE);
        if (!active) return;
        setItems(data?.items ?? []);
        setTotal(data?.total ?? 0);
      } catch (error) {
        if (active) {
          toast.error(error instanceof ApiError ? error.message : "Unable to load activity.");
        }
      } finally {
        if (active) setLoading(false);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, [page]);

  const filteredItems = useMemo(() => {
    if (!search.trim()) return items;
    const needle = search.toLowerCase();
    return items.filter(
      (item) =>
        item.message.toLowerCase().includes(needle) ||
        item.category.toLowerCase().includes(needle) ||
        (item.actor?.name?.toLowerCase().includes(needle) ?? false),
    );
  }, [items, search]);

  return (
    <DashboardShell
      title="Activity"
      subtitle="Human-friendly timeline of what happened in your organization."
    >
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <div className="mb-6 flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl border border-brand-700/50 bg-brand-950/50">
              <Activity size={18} className="text-brand-400" />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-brand-100">Organization timeline</h2>
              <p className="text-sm text-brand-500">
                Invites, assets, scans, reports, and security changes — not forensic audit logs.
              </p>
            </div>
          </div>
        </div>

        <ListSearchBar
          value={search}
          onChange={setSearch}
          placeholder="Search activity..."
          className="mb-6"
        />

        {loading ? (
          <ListSkeleton rows={5} />
        ) : filteredItems.length === 0 ? (
          <EmptyState
            compact
            icon={Activity}
            title={search ? "No matching activity" : "No activity yet"}
            description={
              search
                ? "Try a different search term."
                : "Activity will appear as your team works in this organization."
            }
          />
        ) : (
          <>
            <ActivityTimeline items={filteredItems} />
            {!search && (
              <div className="mt-8 border-t border-brand-800/40 pt-6">
                <Pagination page={page} limit={PAGE_SIZE} total={total} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </motion.div>
    </DashboardShell>
  );
}
