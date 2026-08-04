import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity } from "lucide-react";
import DashboardShell from "../components/DashboardShell";
import FormAlert from "@/shared/components/FormAlert";
import Pagination from "@/shared/components/Pagination";
import ActivityTimeline from "@/shared/components/activity/ActivityTimeline";
import { ApiError } from "@/shared/api/client";
import type { ActivityEvent } from "@/shared/types/activity";
import { organizationsApi } from "../api";

const PAGE_SIZE = 20;

export default function OrganizationActivity() {
  const [items, setItems] = useState<ActivityEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const [alert, setAlert] = useState("");

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
          setAlert(error instanceof ApiError ? error.message : "Unable to load activity.");
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

  return (
    <DashboardShell
      title="Activity"
      subtitle="Human-friendly timeline of what happened in your organization."
    >
      {alert && <FormAlert message={alert} />}

      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        className="glass-panel p-6"
      >
        <div className="mb-6 flex items-center justify-between gap-4">
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
          <Link to="/dashboard" className="btn-ghost text-sm">
            Back to dashboard
          </Link>
        </div>

        {loading ? (
          <div className="animate-pulse space-y-4 py-8">
            <div className="h-4 w-24 rounded bg-brand-900/60" />
            <div className="h-12 rounded bg-brand-900/40" />
            <div className="h-12 rounded bg-brand-900/40" />
          </div>
        ) : (
          <>
            <ActivityTimeline
              items={items}
              emptyMessage="Activity will appear as your team works in this organization."
            />
            <div className="mt-8 border-t border-brand-800/40 pt-6">
              <Pagination
                page={page}
                limit={PAGE_SIZE}
                total={total}
                onPageChange={setPage}
              />
            </div>
          </>
        )}
      </motion.div>
    </DashboardShell>
  );
}
