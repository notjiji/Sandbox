import { useEffect, useState } from "react";
import { Bot, MessageSquare, Sparkles } from "lucide-react";
import { useChatPanel } from "@/features/ai/context/ChatPanelContext";
import { AI_CAPABILITY_PRESETS } from "@/features/ai/constants";
import { organizationsApi } from "@/features/organizations/api";
import AiSummaryPanel from "@/shared/components/AiSummaryPanel";
import SidebarLayout from "@/shared/layouts/SidebarLayout";
import type { OrganizationDetail } from "@/shared/types/organization";
import type { AICapability } from "@/shared/types/ai";

export default function AiAssistant() {
  const [organization, setOrganization] = useState<OrganizationDetail | null>(null);
  const { openChat } = useChatPanel();

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

  const startChat = (capability: AICapability, message?: string) => {
    openChat({ capability, message });
  };

  return (
    <SidebarLayout
      title="AI Assistant"
      subtitle="Security guidance powered by your scan and risk context."
    >
      <AiSummaryPanel
        organizationName={organization?.name ?? "Organization"}
        logoUrl={organization?.logo_url}
        label="AI security summary"
        value="Ready"
        footnote="Open the sidebar assistant to summarize findings, explain risk scores, and get remediation guidance from your organization's scan data."
      />

      <div className="glass-panel mt-6 p-8">
        <div className="flex flex-col gap-6 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-3 text-brand-300">
              <Bot size={24} />
            </div>
            <div>
              <p className="terminal-text text-brand-500">{">"} ai_assistant.init</p>
              <h2 className="mt-2 text-xl font-bold text-brand-100">Security Assistant</h2>
              <p className="mt-2 max-w-xl text-sm text-brand-400">
                Chat in the right sidebar. The assistant reads structured scan results from your
                database — it does not run scanners or invent vulnerabilities.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => startChat("organization_overview")}
            className="btn-primary inline-flex shrink-0 items-center gap-2"
          >
            <MessageSquare size={16} />
            Open chat
          </button>
        </div>

        <div className="mt-8 grid gap-3 sm:grid-cols-2">
          {AI_CAPABILITY_PRESETS.filter((preset) => preset.id !== "general").map((preset) => (
            <button
              key={preset.id}
              type="button"
              onClick={() => startChat(preset.id, preset.defaultMessage || undefined)}
              className="rounded-lg border border-brand-800/50 bg-brand-950/20 p-4 text-left transition hover:border-brand-600/40 hover:bg-brand-900/30"
            >
              <div className="flex items-center gap-2 text-brand-100">
                <Sparkles size={16} className="text-brand-400" />
                <span className="font-medium">{preset.label}</span>
              </div>
              <p className="mt-2 text-sm text-brand-500">{preset.description}</p>
            </button>
          ))}
        </div>
      </div>
    </SidebarLayout>
  );
}
