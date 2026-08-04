export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  const diffMs = Date.now() - date.getTime();
  const diffMin = Math.floor(diffMs / 60_000);
  if (diffMin < 1) return "Just now";
  if (diffMin < 60) return `${diffMin}m ago`;
  const diffHours = Math.floor(diffMin / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d ago`;
  return date.toLocaleDateString();
}

export function formatActionLabel(action: string): string {
  return action
    .split(".")
    .pop()
    ?.replace(/_/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase()) ?? action;
}

export function scanStatusClass(status: string): string {
  switch (status) {
    case "completed":
      return "bg-emerald-500/20 text-emerald-300";
    case "running":
    case "queued":
      return "bg-brand-500/20 text-brand-200";
    case "failed":
      return "bg-rose-500/20 text-rose-300";
    case "cancelled":
      return "bg-brand-800/40 text-brand-500";
    default:
      return "bg-amber-500/20 text-amber-300";
  }
}

export function reportStatusClass(status: string): string {
  switch (status) {
    case "ready":
      return "bg-emerald-500/20 text-emerald-300";
    case "generating":
      return "bg-brand-500/20 text-brand-200";
    case "failed":
      return "bg-rose-500/20 text-rose-300";
    default:
      return "bg-brand-800/40 text-brand-400";
  }
}
