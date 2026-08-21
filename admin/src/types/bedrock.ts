// ============================================================================
// Agent Bedrock - TypeScript types mirroring api/src/schemas/bedrock.py
// ============================================================================

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

// Server-persisted conversation history (see models/bedrock_conversation.py)
// - the same on every device, not client-only state.
export interface BedrockConversation {
  session_id: string
  title: string
  created_at: string
  updated_at: string
}

export interface BedrockChatMessage {
  id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export interface BedrockAuditLogEntry {
  id: number
  action: 'create' | 'update' | 'delete' | string
  resource_type: string
  resource_id: number | null
  old_values: Record<string, unknown> | null
  new_values: Record<string, unknown> | null
  created_at: string
}

export interface BedrockTask {
  id: number
  user_id: number
  title: string
  description: string | null
  status: 'pending' | 'in_progress' | 'done' | 'cancelled' | string
  created_at: string
  updated_at: string
}

export interface BedrockInstructions {
  system_prompt: string
  is_default: boolean
}

export interface BedrockCustomTool {
  id: number
  name: string
  url: string
  headers: Record<string, string> | null
  is_enabled: boolean
  created_at: string
}

// Loosely typed on purpose - passes through whatever AgentCore Memory's API
// returns rather than re-modeling its full response shape (see
// schemas/bedrock.py's BedrockMemoryEventResponse/BedrockMemoryRecordResponse).
export interface BedrockMemoryEvent {
  eventId?: string
  eventTimestamp?: string | number
  payload?: Array<Record<string, unknown>>
  [key: string]: unknown
}

export interface BedrockMemoryRecord {
  memoryRecordId?: string
  content?: Record<string, unknown>
  score?: number
  createdAt?: string | number
  namespaces?: string[]
  [key: string]: unknown
}
