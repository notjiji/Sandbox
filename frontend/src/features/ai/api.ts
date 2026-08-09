import { apiRequest } from "@/shared/api/client";
import type { AIChatRequest, AIChatResponse, ConversationSummary } from "@/shared/types/ai";

export const aiApi = {
  chat: (body: AIChatRequest) =>
    apiRequest<AIChatResponse>("/organizations/ai/chat", {
      method: "POST",
      body,
      auth: true,
    }),

  listConversations: () =>
    apiRequest<{ items: ConversationSummary[]; total: number }>("/organizations/ai/conversations", {
      auth: true,
    }),
};
