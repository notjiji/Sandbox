import { Link, useSearchParams } from "react-router-dom";
import { cn } from "@/shared/lib/utils";

export const SERVER_TABS = [
  { key: "overview", label: "Overview" },
  { key: "metrics", label: "Metrics" },
  { key: "services", label: "Services" },
  { key: "docker", label: "Docker" },
  { key: "security", label: "Security" },
  { key: "findings", label: "Findings" },
  { key: "activity", label: "Activity" },
] as const;

export type ServerTab = (typeof SERVER_TABS)[number]["key"];

export function parseServerTab(value: string | null): ServerTab {
  return SERVER_TABS.some((tab) => tab.key === value) ? (value as ServerTab) : "overview";
}

interface ServerMonitoringTabsProps {
  active: ServerTab;
}

export default function ServerMonitoringTabs({ active }: ServerMonitoringTabsProps) {
  const [searchParams] = useSearchParams();

  return (
    <nav className="flex flex-wrap gap-2">
      {SERVER_TABS.map((tab) => {
        const params = new URLSearchParams(searchParams);
        if (tab.key === "overview") params.delete("tab");
        else params.set("tab", tab.key);
        const query = params.toString();
        return (
          <Link
            key={tab.key}
            to={{ search: query }}
            className={cn(
              "rounded-lg border px-4 py-2 text-sm transition",
              active === tab.key
                ? "border-brand-500/50 bg-brand-900/40 text-brand-100"
                : "border-brand-800/50 text-brand-400 hover:border-brand-600/40 hover:text-brand-200",
            )}
          >
            {tab.label}
          </Link>
        );
      })}
    </nav>
  );
}
