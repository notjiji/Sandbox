import { Link } from "react-router-dom";
import { AlertTriangle, Check, ChevronRight } from "lucide-react";
import type { ActivityEvent } from "@/shared/types/activity";
import { formatRelativeTime } from "@/features/organizations/utils/format";
import { cn } from "@/shared/lib/utils";

function isWarning(item: ActivityEvent): boolean {
  const severity = (item.severity ?? "").toLowerCase();
  if (severity === "warning" || severity === "error" || severity === "critical") return true;
  return item.action.includes("fail") || item.action.includes("plugin_failed");
}

interface ActivityFeedCardProps {
  items: ActivityEvent[];
}

export default function ActivityFeedCard({ items }: ActivityFeedCardProps) {
  if (items.length === 0) {
    return <p className="text-sm text-brand-600">Activity will appear as your team works.</p>;
  }

  return (
    <ul className="space-y-1">
      {items.slice(0, 8).map((item) => {
        const warning = isWarning(item);
        return (
          <li key={item.id}>
            {item.href ? (
              <Link
                to={item.href}
                className="flex items-start gap-3 rounded-lg px-1 py-2 transition hover:bg-brand-900/30"
              >
                <FeedIcon warning={warning} />
                <FeedText item={item} />
              </Link>
            ) : (
              <div className="flex items-start gap-3 px-1 py-2">
                <FeedIcon warning={warning} />
                <FeedText item={item} />
              </div>
            )}
          </li>
        );
      })}
    </ul>
  );
}

function FeedIcon({ warning }: { warning: boolean }) {
  return (
    <span
      className={cn(
        "mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full",
        warning ? "bg-amber-500/15 text-amber-400" : "bg-emerald-500/15 text-emerald-400",
      )}
      aria-hidden
    >
      {warning ? <AlertTriangle size={12} /> : <Check size={12} strokeWidth={3} />}
    </span>
  );
}

function FeedText({ item }: { item: ActivityEvent }) {
  return (
    <div className="min-w-0 flex-1">
      <p className="truncate text-sm text-brand-100">{item.message}</p>
      <p className="mt-0.5 text-xs text-brand-600">{formatRelativeTime(item.created_at)}</p>
    </div>
  );
}

export function ActivityFeedViewAll() {
  return (
    <Link
      to="/organization/activity"
      className="inline-flex items-center gap-1 text-xs text-brand-400 hover:text-brand-200"
    >
      View all
      <ChevronRight size={14} />
    </Link>
  );
}
