import { Link } from "react-router-dom";
import type { LucideIcon } from "lucide-react";
import {
  Activity,
  Bug,
  Building2,
  FileText,
  FolderKanban,
  Layers,
  Radar,
  Shield,
  Users,
} from "lucide-react";
import type { ActivityEvent } from "@/shared/types/activity";
import { formatRelativeTime } from "@/features/organizations/utils/format";
import { cn } from "@/shared/lib/utils";

const CATEGORY_ICONS: Record<string, LucideIcon> = {
  members: Users,
  assets: Layers,
  scans: Radar,
  reports: FileText,
  security: Shield,
  projects: FolderKanban,
  organization: Building2,
  findings: Bug,
  system: Activity,
};

function sameDay(a: Date, b: Date) {
  return (
    a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
  );
}

function dayLabel(iso: string): string {
  const date = new Date(iso);
  const today = new Date();
  const yesterday = new Date();
  yesterday.setDate(today.getDate() - 1);
  if (sameDay(date, today)) return "Today";
  if (sameDay(date, yesterday)) return "Yesterday";
  return date.toLocaleDateString(undefined, {
    weekday: "long",
    month: "short",
    day: "numeric",
  });
}

function groupByDay(items: ActivityEvent[]) {
  const groups: { label: string; items: ActivityEvent[] }[] = [];
  for (const item of items) {
    const label = dayLabel(item.created_at);
    const last = groups[groups.length - 1];
    if (last?.label === label) {
      last.items.push(item);
    } else {
      groups.push({ label, items: [item] });
    }
  }
  return groups;
}

interface ActivityTimelineProps {
  items: ActivityEvent[];
  emptyMessage?: string;
  compact?: boolean;
}

function ActivityTimelineItem({
  item,
  compact,
  isLast,
}: {
  item: ActivityEvent;
  compact?: boolean;
  isLast: boolean;
}) {
  const Icon = CATEGORY_ICONS[item.category] ?? Activity;
  const content = (
    <>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-brand-700/50 bg-brand-950/60",
          compact && "h-7 w-7",
        )}
      >
        <Icon size={compact ? 14 : 16} className="text-brand-400" />
      </div>
      <div className="min-w-0 flex-1 pb-1">
        <p className={cn("text-brand-100", compact ? "text-sm" : "text-sm leading-relaxed")}>
          {item.message}
        </p>
        <p className="mt-1 text-xs text-brand-600">
          {item.actor?.name ? `${item.actor.name} · ` : ""}
          {formatRelativeTime(item.created_at)}
        </p>
      </div>
    </>
  );

  return (
    <li className="relative flex gap-3 pl-1">
      {!isLast && (
        <span
          aria-hidden
          className="absolute left-[1.15rem] top-9 bottom-0 w-px bg-brand-800/60"
        />
      )}
      {item.href ? (
        <Link
          to={item.href}
          className="flex w-full gap-3 rounded-lg border border-transparent px-2 py-2 transition hover:border-brand-700/40 hover:bg-brand-900/20"
        >
          {content}
        </Link>
      ) : (
        <div className="flex w-full gap-3 px-2 py-2">{content}</div>
      )}
    </li>
  );
}

export default function ActivityTimeline({
  items,
  emptyMessage = "No activity yet.",
  compact = false,
}: ActivityTimelineProps) {
  if (items.length === 0) {
    return <p className="text-sm text-brand-600">{emptyMessage}</p>;
  }

  const groups = groupByDay(items);

  return (
    <div className="space-y-6">
      {groups.map((group) => (
        <section key={group.label}>
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-brand-500">
            {group.label}
          </h3>
          <ul className="space-y-1">
            {group.items.map((item, index) => (
              <ActivityTimelineItem
                key={item.id}
                item={item}
                compact={compact}
                isLast={index === group.items.length - 1}
              />
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
