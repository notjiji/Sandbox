import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { Bot, Loader2, Send, Sparkles, X } from "lucide-react";
import { aiApi } from "@/features/ai/api";
import { AI_CAPABILITY_PRESETS } from "@/features/ai/constants";
import { useChatPanel } from "@/features/ai/context/ChatPanelContext";
import { ApiError } from "@/shared/api/client";
import { toast } from "@/shared/lib/toast";
import { cn } from "@/shared/lib/utils";
import type { AICapability, ChatMessage } from "@/shared/types/ai";

function newMessageId() {
  return crypto.randomUUID();
}

function presetForCapability(capability: AICapability) {
  return AI_CAPABILITY_PRESETS.find((item) => item.id === capability);
}

export default function AiChatSidebar() {
  const { projectId: routeProjectId, assetId: routeAssetId } = useParams<{
    projectId?: string;
    assetId?: string;
  }>();
  const {
    open,
    closeChat,
    capability,
    setCapability,
    draftMessage,
    setDraftMessage,
    context,
    setContext,
  } = useChatPanel();

  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setContext((prev) => ({
      ...prev,
      projectId: prev.projectId ?? routeProjectId,
      assetId: prev.assetId ?? routeAssetId,
    }));
  }, [routeProjectId, routeAssetId, setContext]);

  useEffect(() => {
    if (!open) return;
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages, open]);

  const effectiveProjectId = context.projectId ?? routeProjectId;
  const effectiveAssetId = context.assetId ?? routeAssetId;

  const sendMessage = async (rawMessage: string) => {
    const message = rawMessage.trim();
    if (!message || sending) return;

    const preset = presetForCapability(capability);
    if (preset?.requiresProject && !effectiveProjectId) {
      toast.error("Open a project or asset page to use this mode.");
      return;
    }
    if (preset?.requiresAsset && !effectiveAssetId) {
      toast.error("Open an asset page to use this mode.");
      return;
    }

    const userMessage: ChatMessage = {
      id: newMessageId(),
      role: "user",
      content: message,
    };
    const pendingId = newMessageId();
    setMessages((prev) => [
      ...prev,
      userMessage,
      { id: pendingId, role: "assistant", content: "", pending: true },
    ]);
    setDraftMessage("");
    setSending(true);

    try {
      const response = await aiApi.chat({
        message,
        capability,
        conversation_id: conversationId ?? undefined,
        project_id: effectiveProjectId,
        asset_id: effectiveAssetId,
        scan_id: context.scanId,
        finding_id: context.findingId,
        finding_code: context.findingCode,
        audience: preset?.audience,
      });

      setConversationId(response.conversation_id);
      setMessages((prev) =>
        prev.map((item) =>
          item.id === pendingId
            ? {
                id: pendingId,
                role: "assistant",
                content: response.response.answer,
                summary: response.response.summary,
                confidence: response.response.confidence,
                disclaimer: response.response.disclaimer,
                pending: false,
              }
            : item,
        ),
      );
    } catch (err) {
      const text =
        err instanceof ApiError ? err.message : "Could not reach the AI assistant. Try again.";
      toast.error(text);
      setMessages((prev) => prev.filter((item) => item.id !== pendingId));
    } finally {
      setSending(false);
    }
  };

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    void sendMessage(draftMessage);
  };

  const handlePresetSelect = (nextCapability: AICapability) => {
    setCapability(nextCapability);
    const preset = presetForCapability(nextCapability);
    if (preset?.defaultMessage) {
      setDraftMessage(preset.defaultMessage);
    }
  };

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[95] flex justify-end">
      <button
        type="button"
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        aria-label="Close AI assistant"
        onClick={closeChat}
      />
      <aside className="relative z-10 flex h-full w-full max-w-md flex-col border-l border-brand-800/50 bg-void-100 shadow-crt sm:max-w-lg">
        <div className="flex items-start justify-between gap-3 border-b border-brand-800/50 px-5 py-4">
          <div className="flex items-start gap-3">
            <div className="rounded-lg border border-brand-600/40 bg-brand-900/30 p-2 text-brand-300">
              <Sparkles size={18} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-brand-50">Security Assistant</h2>
              <p className="text-xs text-brand-500">Answers from your scan data only</p>
            </div>
          </div>
          <button type="button" onClick={closeChat} className="btn-ghost p-2" aria-label="Close">
            <X size={18} />
          </button>
        </div>

        <div className="border-b border-brand-800/40 px-4 py-3">
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-wide text-brand-600">Mode</p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {AI_CAPABILITY_PRESETS.map((preset) => (
              <button
                key={preset.id}
                type="button"
                onClick={() => handlePresetSelect(preset.id)}
                className={cn(
                  "shrink-0 rounded-full border px-3 py-1.5 text-xs transition",
                  capability === preset.id
                    ? "border-brand-500/60 bg-brand-900/50 text-brand-100"
                    : "border-brand-800/60 bg-brand-950/20 text-brand-400 hover:border-brand-600/40 hover:text-brand-200",
                )}
                title={preset.description}
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        <div ref={scrollRef} className="flex-1 space-y-4 overflow-y-auto px-4 py-4">
          {messages.length === 0 ? (
            <div className="rounded-lg border border-brand-800/40 bg-brand-950/20 p-4 text-sm text-brand-400">
              <p>
                Pick a mode above, then ask a question. The assistant reads findings and scores from
                your database — it does not run scans or invent vulnerabilities.
              </p>
              {(effectiveProjectId || effectiveAssetId) && (
                <p className="mt-3 text-xs text-brand-600">
                  Context:{" "}
                  {[effectiveProjectId && `project`, effectiveAssetId && `asset`]
                    .filter(Boolean)
                    .join(" + ")}
                </p>
              )}
            </div>
          ) : (
            messages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "rounded-lg px-3 py-2.5 text-sm",
                  message.role === "user"
                    ? "ml-8 border border-brand-700/40 bg-brand-900/30 text-brand-100"
                    : "mr-4 border border-brand-800/40 bg-void-200/20 text-brand-200",
                )}
              >
                {message.pending ? (
                  <div className="flex items-center gap-2 text-brand-500">
                    <Loader2 size={16} className="animate-spin" />
                    Thinking...
                  </div>
                ) : (
                  <div className="whitespace-pre-wrap leading-relaxed">{message.content}</div>
                )}
                {message.summary && !message.pending && (
                  <p className="mt-2 border-t border-brand-800/40 pt-2 text-xs text-brand-500">
                    {message.summary}
                  </p>
                )}
                {message.disclaimer && !message.pending && (
                  <p className="mt-2 text-[11px] text-brand-600">{message.disclaimer}</p>
                )}
              </div>
            ))
          )}
        </div>

        <form onSubmit={handleSubmit} className="border-t border-brand-800/50 p-4">
          <label className="block">
            <span className="sr-only">Message</span>
            <textarea
              value={draftMessage}
              onChange={(event) => setDraftMessage(event.target.value)}
              rows={3}
              placeholder="Ask about findings, risk scores, remediation..."
              className="input-field min-h-[72px] resize-none"
              disabled={sending}
            />
          </label>
          <div className="mt-3 flex items-center justify-between gap-3">
            <p className="text-[11px] text-brand-600">Scores and findings come from scanners.</p>
            <button
              type="submit"
              disabled={!draftMessage.trim() || sending}
              className="btn-primary inline-flex items-center gap-2"
            >
              {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
              Send
            </button>
          </div>
        </form>
      </aside>
    </div>
  );
}

export function AiChatFloatingButton() {
  const { open, toggleChat } = useChatPanel();

  if (open) return null;

  return (
    <button
      type="button"
      onClick={toggleChat}
      className="fixed bottom-6 right-6 z-[80] inline-flex items-center gap-2 rounded-full border border-brand-600/50 bg-brand-900/90 px-4 py-3 text-sm font-medium text-brand-100 shadow-glow backdrop-blur-sm transition hover:border-brand-500/70 hover:bg-brand-800/90"
      aria-label="Open AI assistant"
    >
      <Bot size={18} />
      Ask AI
    </button>
  );
}
