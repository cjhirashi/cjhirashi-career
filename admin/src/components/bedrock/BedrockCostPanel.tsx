import React from 'react'
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { Bot } from 'lucide-react'
import { useBedrockModel, useBedrockUsageMetrics } from '@/hooks/useBedrockChat'

const axisTickStyle = { fill: 'var(--text-secondary)', fontSize: 12 }
const formatUSD = (value: number) => `$${value.toFixed(value < 1 ? 4 : 2)}`

/** "Costo del asistente IA" - Agent Bedrock's token usage/cost, logged by
 * `services/bedrock_service.py` on every chat turn (see BedrockUsageLog).
 * Lives on the same metrics dashboard as the search-strategy charts but is
 * its own independent query/loading state, since it has nothing to do with
 * the career-domain data the rest of the page visualizes. */
export const BedrockCostPanel: React.FC = () => {
  const { data: usage, isLoading, isError } = useBedrockUsageMetrics(30)
  const { data: modelStatus } = useBedrockModel()

  // Not configured (503) or genuinely no AWS credentials on the server -
  // this panel just disappears rather than showing an error, same as the
  // chat window's own "not configured" state.
  if (isError) return null

  const labelForModel = (modelId: string) =>
    modelStatus?.available_models.find((m) => m.model_id === modelId)?.label ?? modelId

  return (
    <div className="card">
      <div className="card-header">
        <h2 className="text-base font-semibold text-text flex items-center gap-2">
          <Bot size={17} className="text-primary" aria-hidden="true" />
          Costo del Asistente IA
        </h2>
        <p className="text-text-secondary text-xs mt-1">
          Consumo de tokens de Agent Bedrock (últimos 30 días) - estimado a partir de las tarifas por millón de
          tokens de cada modelo.
        </p>
      </div>
      <div className="card-body space-y-4">
        {isLoading || !usage ? (
          <p className="text-text-secondary text-sm text-center py-6">Cargando...</p>
        ) : usage.by_day.length === 0 ? (
          <p className="text-text-secondary text-sm text-center py-6">
            Todavía no hay conversaciones registradas con el asistente.
          </p>
        ) : (
          <>
            <div className="stat-card inline-block">
              <p className="text-text-secondary text-sm font-medium">Total (30 días)</p>
              <p className="text-3xl font-bold mono mt-2" style={{ color: 'var(--primary-color)' }}>
                {formatUSD(usage.total_estimated_cost_usd)}
              </p>
            </div>

            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={usage.by_day} margin={{ left: 0, right: 12 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                <XAxis dataKey="day" tick={axisTickStyle} />
                <YAxis tick={axisTickStyle} tickFormatter={formatUSD} width={70} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-glass)', border: '1px solid var(--border)', borderRadius: 8 }}
                  formatter={(value: number) => formatUSD(value)}
                />
                <Area
                  type="monotone"
                  dataKey="estimated_cost_usd"
                  name="Costo estimado"
                  stroke="var(--primary-color)"
                  fill="var(--primary-color)"
                  fillOpacity={0.15}
                />
              </AreaChart>
            </ResponsiveContainer>

            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-text-secondary text-xs">
                    <th className="text-left font-medium pb-2">Modelo</th>
                    <th className="text-right font-medium pb-2">Turnos</th>
                    <th className="text-right font-medium pb-2">Tokens entrada</th>
                    <th className="text-right font-medium pb-2">Tokens salida</th>
                    <th className="text-right font-medium pb-2">Costo</th>
                  </tr>
                </thead>
                <tbody>
                  {usage.by_model.map((row) => (
                    <tr key={row.model_id} className="border-t" style={{ borderColor: 'var(--border-glass)' }}>
                      <td className="py-2 text-text">{labelForModel(row.model_id)}</td>
                      <td className="py-2 text-right mono text-text-secondary">{row.turns}</td>
                      <td className="py-2 text-right mono text-text-secondary">{row.input_tokens.toLocaleString()}</td>
                      <td className="py-2 text-right mono text-text-secondary">{row.output_tokens.toLocaleString()}</td>
                      <td className="py-2 text-right mono text-text font-semibold">
                        {formatUSD(row.estimated_cost_usd)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
