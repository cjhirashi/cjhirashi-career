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
  daily_budget_usd?: number
  daily_spent_usd?: number
  daily_remaining_usd?: number
}

/** Where the chat UI lives — general full-page vs contextual sidebar. */
export type BedrockChatSurface = 'contextual' | 'general'

/** Session bucket stored on the server (see bedrock_conversation.session_type). */
export type BedrockSessionType = 'contextual' | 'general'

/**
 * Page context sent with contextual chat turns so the harness can tailor
 * prompts and model selection (mirror of BedrockChatRequest.page_context).
 */
export interface BedrockPageContext {
  route: string
  page_title?: string
  resource_key?: string
  domain_key?: string
  /** Named chat profile key — resolved to a model id via chatSectionProfiles.ts */
  chat_profile?: string
}

/** Full payload for POST /bedrock/chat (mirror of schemas/bedrock.py). */
export interface BedrockChatAttachment {
  file_id: number
  filename: string
  mime_type?: string
  url?: string
}

export interface BedrockChatRequest {
  session_id: string
  message: string
  chat_surface?: BedrockChatSurface
  page_context?: BedrockPageContext | null
  model_id?: string | null
  agent_profile_id?: string | null
  attachments?: BedrockChatAttachment[] | null
}

// Server-persisted conversation history (see models/bedrock_conversation.py)
// - the same on every device, not client-only state.
export interface BedrockConversation {
  session_id: string
  title: string
  session_type: BedrockSessionType
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
