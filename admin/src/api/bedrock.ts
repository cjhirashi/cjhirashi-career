import { axiosInstance } from './client'
import {
  BedrockChatResponse,
  BedrockModelStatus,
  BedrockUsageMetrics,
} from '@/types/bedrock'

/**
 * Client for Agent Bedrock (chat, model switching, usage/cost metrics).
 *
 * `chat` only ever sends the newest message plus a `sessionId` - the
 * AgentCore Harness backing this owns the conversation history server-side
 * (see api/src/services/bedrock_service.py), so there's no message history
 * to resend on every turn like a plain Converse-API chat would need.
 */
export const bedrockApi = {
  chat: async (sessionId: string, message: string): Promise<BedrockChatResponse> => {
    const response = await axiosInstance.post<BedrockChatResponse>('/bedrock/chat', {
      session_id: sessionId,
      message,
    })
    return response.data
  },

  getModel: async (): Promise<BedrockModelStatus> => {
    const response = await axiosInstance.get<BedrockModelStatus>('/bedrock/model')
    return response.data
  },

  switchModel: async (modelId: string): Promise<BedrockModelStatus> => {
    const response = await axiosInstance.post<BedrockModelStatus>('/bedrock/model', {
      model_id: modelId,
    })
    return response.data
  },

  usageMetrics: async (days = 30): Promise<BedrockUsageMetrics> => {
    const response = await axiosInstance.get<BedrockUsageMetrics>('/bedrock/usage-metrics', {
      params: { days },
    })
    return response.data
  },
}
