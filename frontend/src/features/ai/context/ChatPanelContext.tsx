import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
} from "react";
import type { AICapability, ChatContext } from "@/shared/types/ai";

export interface OpenChatOptions {
  capability?: AICapability;
  message?: string;
  context?: ChatContext;
}

interface ChatPanelContextValue {
  open: boolean;
  capability: AICapability;
  draftMessage: string;
  context: ChatContext;
  openChat: (options?: OpenChatOptions) => void;
  closeChat: () => void;
  toggleChat: () => void;
  setCapability: (capability: AICapability) => void;
  setDraftMessage: (message: string) => void;
  setContext: Dispatch<SetStateAction<ChatContext>>;
}

const ChatPanelContext = createContext<ChatPanelContextValue | null>(null);

export function ChatPanelProvider({ children }: { children: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [capability, setCapability] = useState<AICapability>("general");
  const [draftMessage, setDraftMessage] = useState("");
  const [context, setContext] = useState<ChatContext>({});

  const openChat = useCallback((options?: OpenChatOptions) => {
    if (options?.capability) setCapability(options.capability);
    if (options?.message !== undefined) setDraftMessage(options.message);
    if (options?.context) setContext((prev) => ({ ...prev, ...options.context }));
    setOpen(true);
  }, []);

  const closeChat = useCallback(() => setOpen(false), []);

  const toggleChat = useCallback(() => setOpen((value) => !value), []);

  const value = useMemo(
    () => ({
      open,
      capability,
      draftMessage,
      context,
      openChat,
      closeChat,
      toggleChat,
      setCapability,
      setDraftMessage,
      setContext,
    }),
    [open, capability, draftMessage, context, openChat, closeChat, toggleChat],
  );

  return <ChatPanelContext.Provider value={value}>{children}</ChatPanelContext.Provider>;
}

export function useChatPanel() {
  const ctx = useContext(ChatPanelContext);
  if (!ctx) {
    throw new Error("useChatPanel must be used within ChatPanelProvider");
  }
  return ctx;
}

export function useChatPanelOptional() {
  return useContext(ChatPanelContext);
}
