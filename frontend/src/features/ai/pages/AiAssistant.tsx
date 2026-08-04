import { useEffect, useState } from "react";
import { Bot } from "lucide-react";
import { organizationsApi } from "@/features/organizations/api";
import AiSummaryPanel from "@/shared/components/AiSummaryPanel";
import SidebarLayout from "@/shared/layouts/SidebarLayout";
import type { OrganizationDetail } from "@/shared/types/organization";

export default function AiAssistant() {
  const [organization, setOrganization] = useState<OrganizationDetail | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const detail = await organizationsApi.getCurrent();
        if (active) setOrganization(detail);
      } catch {
        if (active) setOrganization(null);
      }
    }

    void load();
    return () => {
      active = false;
    };
  }, []);

  return (
    <SidebarLayout
      title="AI Assistant"
      subtitle="Security guidance powered by your scan and risk context."
    >
      <AiSummaryPanel
        organizationName={organization?.name ?? "Organization"}
        logoUrl={organization?.logo_url}
        label="AI security summary"
        value="Coming soon"
        footnote="The AI Assistant will summarize findings, explain risk scores, and suggest remediation steps based on your organization's assets and scan history."
      />

      <div className="glass-panel mt-6 p-8">
        <div className="flex items-start gap-4">
          <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-3 text-brand-300">
            <Bot size={24} />
          </div>
          <div>
            <p className="terminal-text text-brand-500">{">"} ai_assistant.init</p>
            <h2 className="mt-2 text-xl font-bold text-brand-100">Coming soon</h2>
            <p className="mt-2 max-w-xl text-sm text-brand-400">
              Ask questions about open findings, compare scan results, and generate executive
              summaries branded with your organization logo.
            </p>
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
