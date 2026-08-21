import React from 'react'
import { BedrockCostPanel } from '@/components/bedrock/BedrockCostPanel'

export const AgentMetricsPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Métricas del Agente</h1>
        <p className="text-text-secondary mt-2">Consumo de tokens y costo estimado de Agent Bedrock.</p>
      </div>
      <BedrockCostPanel />
    </div>
  )
}
