export type AICapability =
  | "explain_finding"
  | "explain_risk_score"
  | "remediation"
  | "executive_summary"
  | "technical_summary"
  | "compare_scans"
  | "asset_summary"
  | "organization_overview"
  | "general";

export interface AIChatRequest {
  message: string;
  capability?: AICapability;
  conversation_id?: string;
  project_id?: string;
  asset_id?: string;
  scan_id?: string;
  finding_id?: string;
  finding_code?: string;
  audience?: "executive" | "technical";
}

export interface AIResponsePayload {
  answer: string;
  summary?: string | null;
  references?: string[];
  related_findings?: string[];
  confidence?: "high" | "medium" | "low";
  disclaimer?: string | null;
}

export interface AIChatResponse {
  conversation_id: string;
  capability: AICapability;
  response: AIResponsePayload;
  context_keys?: string[];
  model?: string | null;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  summary?: string | null;
  confidence?: "high" | "medium" | "low";
  disclaimer?: string | null;
  pending?: boolean;
}

export interface ChatContext {
  projectId?: string;
  assetId?: string;
  scanId?: string;
  findingId?: string;
  findingCode?: string;
}

export interface ConversationSummary {
  id: string;
  title: string | null;
  created_at: string;
  updated_at: string;
}
