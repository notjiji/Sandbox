import { Bot } from "lucide-react";
import SidebarLayout from "@/shared/layouts/SidebarLayout";

export default function AiAssistant() {
  return (
    <SidebarLayout
      title="AI Assistant"
      subtitle="Security guidance powered by your scan and risk context."
    >
      <div className="glass-panel p-8">
        <div className="flex items-start gap-4">
          <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-3 text-brand-300">
            <Bot size={24} />
          </div>
          <div>
            <p className="terminal-text text-brand-500">{">"} ai_assistant.init</p>
            <h2 className="mt-2 text-xl font-bold text-brand-100">Coming soon</h2>
            <p className="mt-2 max-w-xl text-sm text-brand-400">
              The AI Assistant will summarize findings, explain risk scores, and suggest remediation
              steps based on your organization&apos;s assets and scan history.
            </p>
          </div>
        </div>
      </div>
    </SidebarLayout>
  );
}
