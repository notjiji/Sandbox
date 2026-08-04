import { Bot } from "lucide-react";
import OrganizationLogo from "@/shared/components/OrganizationLogo";
import { cn } from "@/shared/lib/utils";

interface AiSummaryPanelProps {
  organizationName: string;
  logoUrl?: string | null;
  label: string;
  value: string;
  footnote?: string;
  className?: string;
}

export default function AiSummaryPanel({
  organizationName,
  logoUrl,
  label,
  value,
  footnote = "Available in a future release",
  className,
}: AiSummaryPanelProps) {
  return (
    <div className={cn("glass-panel flex items-start gap-4 p-5", className)}>
      <OrganizationLogo name={organizationName} logoUrl={logoUrl} size="md" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-2">
          <Bot size={16} className="shrink-0 text-brand-400" />
          <p className="text-sm text-brand-500">{label}</p>
        </div>
        <p className="mt-1 text-lg font-medium text-brand-100">{value}</p>
        {footnote && <p className="mt-1 text-xs text-brand-600">{footnote}</p>}
      </div>
    </div>
  );
}
