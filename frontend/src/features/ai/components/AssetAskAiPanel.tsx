import { useState } from "react";
import { ArrowDown, Bot, Send, Sparkles } from "lucide-react";
import { toast } from "@/shared/lib/toast";
import { cn } from "@/shared/lib/utils";
import { ASSET_AI_EXAMPLE_PROMPTS } from "../constants";

interface AssetAskAiPanelProps {
  assetName: string;
  className?: string;
  variant?: "full" | "compact";
}

const PHASE_NOTE =
  "AI responses will use this asset's scans, findings, and risk history. Available in Phase 7.";

export default function AssetAskAiPanel({
  assetName,
  className,
  variant = "full",
}: AssetAskAiPanelProps) {
  const [query, setQuery] = useState("");
  const [expanded, setExpanded] = useState(variant === "full");

  const notifyComingSoon = (prompt?: string) => {
    if (prompt) setQuery(prompt);
    toast.info("AI assistant is coming in Phase 7. Your question will be ready to send then.");
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) return;
    notifyComingSoon(trimmed);
  };

  if (variant === "compact" && !expanded) {
    return (
      <button
        type="button"
        onClick={() => setExpanded(true)}
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
        <span className="rounded-full border border-brand-700/50 bg-brand-900/40 px-2.5 py-0.5 text-xs text-brand-400">
          Phase 7
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
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-lg font-semibold text-brand-50">Ask AI</h2>
              <span className="rounded-full border border-brand-700/50 bg-brand-900/40 px-2.5 py-0.5 text-xs text-brand-400">
                Phase 7
              </span>
            </div>
            <p className="mt-1 text-sm text-brand-400">
              Get instant answers about <span className="text-brand-200">{assetName}</span>
            </p>
          </div>
        </div>
        {variant === "compact" && (
          <button
            type="button"
            onClick={() => setExpanded(false)}
            className="text-xs text-brand-500 hover:text-brand-300"
          >
            Collapse
          </button>
        )}
      </div>

      <div className="space-y-5 px-5 py-5">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="min-w-0 flex-1">
            <span className="sr-only">Ask AI about this asset</span>
            <textarea
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              rows={variant === "full" ? 2 : 1}
              placeholder="Ask about scans, risk, findings, DNS, certificates..."
              className="input-field min-h-[44px] resize-none"
            />
          </label>
          <button
            type="submit"
            disabled={!query.trim()}
            className="btn-primary inline-flex shrink-0 items-center justify-center gap-2 sm:w-auto"
          >
            <Send size={16} />
            Ask
          </button>
        </form>

        <div>
          <p className="mb-3 text-xs font-semibold uppercase tracking-wide text-brand-500">Examples</p>
          {variant === "full" ? (
            <ul className="space-y-0">
              {ASSET_AI_EXAMPLE_PROMPTS.map((prompt, index) => (
                <li key={prompt}>
                  <button
                    type="button"
                    onClick={() => notifyComingSoon(prompt)}
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
          ) : (
            <div className="flex flex-wrap gap-2">
              {ASSET_AI_EXAMPLE_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => notifyComingSoon(prompt)}
                  className="rounded-full border border-brand-800/60 bg-brand-950/30 px-3 py-1.5 text-xs text-brand-300 transition hover:border-brand-500/40 hover:text-brand-100"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>

        <p className="text-xs text-brand-600">{PHASE_NOTE}</p>
      </div>
    </div>
  );
}
