export const ASSET_AI_EXAMPLE_PROMPTS = [
  "Explain this asset.",
  "Summarize latest scan.",
  "Why is risk increasing?",
  "How do I secure this server?",
  "Explain DNS findings.",
] as const;

export type AssetAiExamplePrompt = (typeof ASSET_AI_EXAMPLE_PROMPTS)[number];
