import type { AICapability } from "@/shared/types/ai";

export const ASSET_AI_EXAMPLE_PROMPTS = [
  "Explain this asset.",
  "Summarize latest scan.",
  "Why is risk increasing?",
  "How do I secure this server?",
  "Explain DNS findings.",
] as const;

export type AssetAiExamplePrompt = (typeof ASSET_AI_EXAMPLE_PROMPTS)[number];

export interface AICapabilityPreset {
  id: AICapability;
  label: string;
  description: string;
  defaultMessage: string;
  requiresAsset?: boolean;
  requiresProject?: boolean;
  audience?: "executive" | "technical";
}

export const AI_CAPABILITY_PRESETS: AICapabilityPreset[] = [
  {
    id: "explain_finding",
    label: "Explain finding",
    description: "What a finding means and why it matters",
    defaultMessage: "Explain this finding and its impact.",
    requiresProject: true,
  },
  {
    id: "explain_risk_score",
    label: "Explain risk score",
    description: "Why the score is what it is",
    defaultMessage: "Why is our risk score at this level?",
    requiresAsset: true,
    requiresProject: true,
  },
  {
    id: "remediation",
    label: "Remediation guide",
    description: "Steps to fix a finding",
    defaultMessage: "How do I fix this finding?",
    requiresProject: true,
  },
  {
    id: "executive_summary",
    label: "Executive summary",
    description: "Non-technical overview for leadership",
    defaultMessage: "Summarize our security posture for executives.",
    audience: "executive",
  },
  {
    id: "technical_summary",
    label: "Technical summary",
    description: "Engineer-focused detail from scan data",
    defaultMessage: "Provide a technical security summary.",
    audience: "technical",
    requiresAsset: true,
    requiresProject: true,
  },
  {
    id: "compare_scans",
    label: "Compare scans",
    description: "What changed since the last scan",
    defaultMessage: "What changed since the previous scan?",
    requiresAsset: true,
    requiresProject: true,
  },
  {
    id: "asset_summary",
    label: "Asset summary",
    description: "Latest scan, findings, and trend for one asset",
    defaultMessage: "Summarize this asset's security status.",
    requiresAsset: true,
    requiresProject: true,
  },
  {
    id: "organization_overview",
    label: "Organization overview",
    description: "Org-wide posture and priorities",
    defaultMessage: "Give me an overview of our organization security posture.",
  },
  {
    id: "general",
    label: "General question",
    description: "Ask anything about your scan data",
    defaultMessage: "",
  },
];
