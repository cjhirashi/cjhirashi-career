import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor, fireEvent } from '../utils'
import { AgentPromptsSettingsPage } from '@/pages/AgentPromptsSettingsPage'
import { bedrockApi } from '@/api/bedrock'
import { BedrockInstructions } from '@/types/bedrock'

vi.mock('@/api/bedrock')

const mockedApi = vi.mocked(bedrockApi)

const sampleInstructions: BedrockInstructions = {
  system_prompt: 'Eres el orquestador de cjhirashi-career.',
  system_prompt_is_default: true,
  global_rules: 'No inventes datos. Asigna metodologías según el dominio.',
  global_rules_is_default: true,
}

describe('AgentPromptsSettingsPage', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    mockedApi.getInstructions.mockResolvedValue(sampleInstructions)
  })

  it('loads and displays both the system prompt and global rules cards', async () => {
    render(<AgentPromptsSettingsPage />)
    await waitFor(() =>
      expect(screen.getByLabelText(/instrucciones base/i)).toHaveValue(sampleInstructions.system_prompt)
    )
    expect(screen.getByLabelText(/reglas fijas que aplican a todos los agentes/i)).toHaveValue(
      sampleInstructions.global_rules
    )
    expect(screen.getAllByText('Usando el predeterminado')).toHaveLength(2)
  })

  it('saves an edited system prompt', async () => {
    mockedApi.updateInstructions.mockResolvedValue({
      ...sampleInstructions,
      system_prompt: 'Nuevo prompt',
      system_prompt_is_default: false,
    })
    render(<AgentPromptsSettingsPage />)
    await waitFor(() => expect(screen.getByLabelText(/instrucciones base/i)).toBeInTheDocument())

    fireEvent.change(screen.getByLabelText(/instrucciones base/i), { target: { value: 'Nuevo prompt' } })
    fireEvent.click(screen.getAllByRole('button', { name: /guardar/i })[0])

    await waitFor(() =>
      expect(mockedApi.updateInstructions).toHaveBeenCalledWith('Nuevo prompt', expect.anything())
    )
  })

  it('resets the global rules card to default', async () => {
    mockedApi.getInstructions.mockResolvedValue({
      ...sampleInstructions,
      global_rules: 'Regla personalizada',
      global_rules_is_default: false,
    })
    mockedApi.updateGlobalRules.mockResolvedValue({
      ...sampleInstructions,
      global_rules: 'Regla por defecto',
      global_rules_is_default: true,
    })
    render(<AgentPromptsSettingsPage />)
    await waitFor(() =>
      expect(screen.getByLabelText(/reglas fijas que aplican a todos los agentes/i)).toHaveValue(
        'Regla personalizada'
      )
    )

    const resetButtons = screen.getAllByRole('button', { name: /restablecer al predeterminado/i })
    fireEvent.click(resetButtons[1])

    await waitFor(() =>
      expect(mockedApi.updateGlobalRules).toHaveBeenCalledWith(null, expect.anything())
    )
  })
})
