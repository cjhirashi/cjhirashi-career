// ============================================================================
// Agent Bedrock - TypeScript types mirroring api/src/schemas/bedrock.py
// ============================================================================

export interface BedrockChatResponse {
  reply: string
  affected_resources: string[]
}

export interface BedrockModelOption {
  model_id: string
  label: string
  price_input_per_million: number
  price_output_per_million: number
}

export interface BedrockModelStatus {
  current_model_id: string
  available_models: BedrockModelOption[]
}

export interface BedrockUsageByModel {
  model_id: string
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
  turns: number
}

export interface BedrockUsageByDay {
  day: string
  input_tokens: number
  output_tokens: number
  estimated_cost_usd: number
}

export interface BedrockUsageMetrics {
  by_model: BedrockUsageByModel[]
  by_day: BedrockUsageByDay[]
  total_estimated_cost_usd: number
}

// Client-side chat message shape - not the same as the backend's request
// body (which only ever carries the newest message, see bedrockChatStore.ts).
export interface BedrockChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  createdAt: string
}
