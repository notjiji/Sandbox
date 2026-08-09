import { ArrowDown, Bot, Send, Sparkles } from "lucide-react";
import { useParams } from "react-router-dom";
import { useChatPanel } from "@/features/ai/context/ChatPanelContext";
import { cn } from "@/shared/lib/utils";
import { ASSET_AI_EXAMPLE_PROMPTS } from "../constants";
import type { AICapability } from "@/shared/types/ai";

interface AssetAskAiPanelProps {
  assetName: string;
  className?: string;
  variant?: "full" | "compact";
}

export default function AssetAskAiPanel({
  assetName,
  className,
  variant = "full",
}: AssetAskAiPanelProps) {
  const { projectId, assetId } = useParams<{ projectId: string; assetId: string }>();
  const { openChat } = useChatPanel();

  const launchChat = (message?: string, capability: AICapability = "asset_summary") => {
    openChat({
      capability,
      message: message ?? "",
      context: { projectId, assetId },
    });
  };

  if (variant === "compact") {
    return (
      <button
        type="button"
        onClick={() => launchChat("Summarize this asset's security status.")}
        className={cn(
          "glass-panel flex w-full items-center justify-between gap-3 p-4 text-left transition hover:border-brand-500/40",
          className,
        )}
      >
        <div className="flex items-center gap-3">
          <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-2 text-brand-300">
            <Bot size={18} />
          </div>
          <div>
            <p className="font-medium text-brand-100">Ask AI</p>
            <p className="text-xs text-brand-500">Get answers about {assetName}</p>
          </div>
        </div>
        <span className="rounded-full border border-brand-600/40 bg-brand-900/40 px-2.5 py-0.5 text-xs text-brand-300">
          Open
        </span>
      </button>
    );
  }

  return (
    <div
      className={cn(
        "glass-panel overflow-hidden border-brand-600/20 bg-gradient-to-br from-brand-950/40 via-void-200/10 to-void-200/5",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-4 border-b border-brand-800/40 px-5 py-4">
        <div className="flex items-start gap-3">
          <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-2.5 text-brand-300">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-brand-50">Ask AI</h2>
            <p className="mt-1 text-sm text-brand-400">
              Get instant answers about <span className="text-brand-200">{assetName}</span>
            </p>
          </div>
        </div>
      </div>

      <div className="space-y-5 px-5 py-5">
        <button
          type="button"
          onClick={() => launchChat()}
          className="btn-primary inline-flex w-full items-center justify-center gap-2 sm:w-auto"
        >
          <Send size={16} />
          Open assistant
        </button>

        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-brand-500">Examples</p>
          <ul className="space-y-0">
            {ASSET_AI_EXAMPLE_PROMPTS.map((prompt, index) => (
              <li key={prompt}>
                <button
                  type="button"
                  onClick={() => launchChat(prompt)}
                  className="w-full rounded-lg px-3 py-2.5 text-left text-sm text-brand-200 transition hover:bg-brand-900/40 hover:text-brand-50"
                >
                  {prompt}
                </button>
                {index < ASSET_AI_EXAMPLE_PROMPTS.length - 1 && (
                  <div className="flex justify-center py-0.5 text-brand-700" aria-hidden>
                    <ArrowDown size={14} />
                  </div>
                )}
              </li>
            ))}
          </ul>
        </div>

        <p className="text-xs text-brand-600">
          Answers are generated from this asset&apos;s scans, findings, and risk history in your database.
        </p>
      </div>
    </div>
  );
}
