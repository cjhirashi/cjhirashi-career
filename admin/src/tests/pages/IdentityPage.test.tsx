import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '../utils'
import { IdentityPage } from '@/pages/IdentityPage'

describe('IdentityPage', () => {
  describe('rendering', () => {
    it('should render page title', () => {
      render(<IdentityPage />)
      expect(screen.getByText('Professional Identity')).toBeInTheDocument()
    })

    it('should render page description', () => {
      render(<IdentityPage />)
      expect(screen.getByText('Define your professional identity and unique value')).toBeInTheDocument()
    })

    it('should render all section headers', () => {
      render(<IdentityPage />)
      expect(screen.getByText('Your IKIGAI')).toBeInTheDocument()
      expect(screen.getByText('Key Differentiators')).toBeInTheDocument()
      expect(screen.getByText('Professional Narrative')).toBeInTheDocument()
      expect(screen.getByText('Value Proposition')).toBeInTheDocument()
    })
  })

  describe('IKIGAI section', () => {
    it('should render all four IKIGAI fields', () => {
      render(<IdentityPage />)
      expect(screen.getByLabelText('What do I do?')).toBeInTheDocument()
      expect(screen.getByLabelText('What do I love?')).toBeInTheDocument()
      expect(screen.getByLabelText('What am I good at?')).toBeInTheDocument()
      expect(screen.getByLabelText('What pays?')).toBeInTheDocument()
    })

    it('should have proper placeholder text for IKIGAI fields', () => {
      render(<IdentityPage />)
      expect(screen.getByPlaceholderText(/Describe your professional activities/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/What aspects of work bring you joy/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/List your strengths and expertise/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/What market value do you have/i)).toBeInTheDocument()
    })

    it('should update IKIGAI field values', () => {
      render(<IdentityPage />)
      const whatDoField = screen.getByLabelText('What do I do?') as HTMLTextAreaElement
      fireEvent.change(whatDoField, { target: { value: 'Build scalable systems' } })
      expect(whatDoField.value).toBe('Build scalable systems')
    })

    it('should handle all IKIGAI fields independently', () => {
      render(<IdentityPage />)
      const doField = screen.getByLabelText('What do I do?') as HTMLTextAreaElement
      const loveField = screen.getByLabelText('What do I love?') as HTMLTextAreaElement

      fireEvent.change(doField, { target: { value: 'Engineering' } })
      fireEvent.change(loveField, { target: { value: 'Problem solving' } })

      expect(doField.value).toBe('Engineering')
      expect(loveField.value).toBe('Problem solving')
    })
  })

  describe('Differentiators section', () => {
    it('should render differentiators textarea', () => {
      render(<IdentityPage />)
      expect(screen.getByLabelText('Your Top 3-5 Differentiators')).toBeInTheDocument()
    })

    it('should have helper text for differentiators', () => {
      render(<IdentityPage />)
      expect(screen.getByText('Enter one per line')).toBeInTheDocument()
    })

    it('should handle single differentiator', () => {
      render(<IdentityPage />)
      const differentiatorField = screen.getByLabelText('Your Top 3-5 Differentiators') as HTMLTextAreaElement
      fireEvent.change(differentiatorField, { target: { value: 'Cloud expertise' } })
      expect(differentiatorField.value).toBe('Cloud expertise')
    })

    it('should handle multiple differentiators', () => {
      render(<IdentityPage />)
      const differentiatorField = screen.getByLabelText('Your Top 3-5 Differentiators') as HTMLTextAreaElement
      fireEvent.change(differentiatorField, {
        target: {
          value: 'Cloud expertise\nTeam leadership\nArchitecture design',
        },
      })
      expect(differentiatorField.value).toContain('Cloud expertise')
      expect(differentiatorField.value).toContain('Team leadership')
      expect(differentiatorField.value).toContain('Architecture design')
    })
  })

  describe('Professional Narrative section', () => {
    it('should render narrative textarea', () => {
      render(<IdentityPage />)
      expect(screen.getByLabelText('Your Story')).toBeInTheDocument()
    })

    it('should update narrative text', () => {
      render(<IdentityPage />)
      const narrativeField = screen.getByLabelText('Your Story') as HTMLTextAreaElement
      const storyText = 'I am a software engineer with 10+ years of experience...'
      fireEvent.change(narrativeField, { target: { value: storyText } })
      expect(narrativeField.value).toBe(storyText)
    })

    it('should display character count', () => {
      render(<IdentityPage />)
      expect(screen.getByText('0 characters')).toBeInTheDocument()
    })

    it('should update character count when typing', () => {
      render(<IdentityPage />)
      const narrativeField = screen.getByLabelText('Your Story') as HTMLTextAreaElement
      fireEvent.change(narrativeField, { target: { value: 'Hello World' } })
      expect(screen.getByText('11 characters')).toBeInTheDocument()
    })

    it('should handle long narrative text', () => {
      render(<IdentityPage />)
      const longText = 'A'.repeat(500)
      const narrativeField = screen.getByLabelText('Your Story') as HTMLTextAreaElement
      fireEvent.change(narrativeField, { target: { value: longText } })
      expect(screen.getByText('500 characters')).toBeInTheDocument()
    })
  })

  describe('Value Proposition section', () => {
    it('should render value proposition textarea', () => {
      render(<IdentityPage />)
      expect(screen.getByLabelText('Your Value Proposition')).toBeInTheDocument()
    })

    it('should update value proposition', () => {
      render(<IdentityPage />)
      const valuePropField = screen.getByLabelText('Your Value Proposition') as HTMLTextAreaElement
      const valueProp = 'I deliver scalable, maintainable solutions'
      fireEvent.change(valuePropField, { target: { value: valueProp } })
      expect(valuePropField.value).toBe(valueProp)
    })

    it('should have proper placeholder text', () => {
      render(<IdentityPage />)
      expect(screen.getByPlaceholderText(/Clearly state the benefits and outcomes/i)).toBeInTheDocument()
    })
  })

  describe('form submission', () => {
    it('should render submit button', () => {
      render(<IdentityPage />)
      expect(screen.getByRole('button', { name: /Save Identity/i })).toBeInTheDocument()
    })

    it('should render cancel button', () => {
      render(<IdentityPage />)
      expect(screen.getByRole('button', { name: /Cancel/i })).toBeInTheDocument()
    })

    it('should handle form submission', () => {
      const consoleSpy = vi.spyOn(console, 'log')
      render(<IdentityPage />)

      const whatDoField = screen.getByLabelText('What do I do?') as HTMLTextAreaElement
      fireEvent.change(whatDoField, { target: { value: 'Build systems' } })

      const submitButton = screen.getByRole('button', { name: /Save Identity/i })
      fireEvent.click(submitButton)

      expect(consoleSpy).toHaveBeenCalledWith(
        'Submit identity form:',
        expect.objectContaining({
          ikigai_what_do_i_do: 'Build systems',
        })
      )

      consoleSpy.mockRestore()
    })

    it('should prevent default form submission', () => {
      render(<IdentityPage />)
      const form = screen.getByLabelText('What do I do?').closest('form')
      const submitEvent = new Event('submit', { bubbles: true, cancelable: true })
      const preventDefaultSpy = vi.spyOn(submitEvent, 'preventDefault')

      form?.dispatchEvent(submitEvent)
      expect(preventDefaultSpy).toHaveBeenCalled()
    })
  })

  describe('form state management', () => {
    it('should initialize form with empty values', () => {
      render(<IdentityPage />)
      const doField = screen.getByLabelText('What do I do?') as HTMLTextAreaElement
      const loveField = screen.getByLabelText('What do I love?') as HTMLTextAreaElement
      expect(doField.value).toBe('')
      expect(loveField.value).toBe('')
    })

    it('should persist form state while editing', () => {
      render(<IdentityPage />)
      const doField = screen.getByLabelText('What do I do?') as HTMLTextAreaElement

      fireEvent.change(doField, { target: { value: 'First input' } })
      expect(doField.value).toBe('First input')

      fireEvent.change(doField, { target: { value: 'First input updated' } })
      expect(doField.value).toBe('First input updated')
    })

    it('should handle form reset', () => {
      render(<IdentityPage />)
      const doField = screen.getByLabelText('What do I do?') as HTMLTextAreaElement

      fireEvent.change(doField, { target: { value: 'Some text' } })
      expect(doField.value).toBe('Some text')

      // Reset form would typically be done via cancel button
      fireEvent.change(doField, { target: { value: '' } })
      expect(doField.value).toBe('')
    })
  })

  describe('form validation', () => {
    it('should accept any text input (no validation)', () => {
      render(<IdentityPage />)
      const doField = screen.getByLabelText('What do I do?') as HTMLTextAreaElement
      const specialChars = '!@#$%^&*()'
      fireEvent.change(doField, { target: { value: specialChars } })
      expect(doField.value).toBe(specialChars)
    })

    it('should handle empty form submission', () => {
      const consoleSpy = vi.spyOn(console, 'log')
      render(<IdentityPage />)
      const submitButton = screen.getByRole('button', { name: /Save Identity/i })
      fireEvent.click(submitButton)

      expect(consoleSpy).toHaveBeenCalledWith(
        'Submit identity form:',
        expect.objectContaining({
          ikigai_what_do_i_do: '',
        })
      )

      consoleSpy.mockRestore()
    })
  })

  describe('accessibility', () => {
    it('should have proper labels for all inputs', () => {
      render(<IdentityPage />)
      expect(screen.getByLabelText('What do I do?')).toBeInTheDocument()
      expect(screen.getByLabelText('Your Story')).toBeInTheDocument()
      expect(screen.getByLabelText('Your Value Proposition')).toBeInTheDocument()
    })

    it('should have descriptive headings', () => {
      render(<IdentityPage />)
      expect(screen.getByText(/Your IKIGAI/i)).toBeInTheDocument()
      expect(screen.getByText(/Professional Narrative/i)).toBeInTheDocument()
    })

    it('should have form semantic structure', () => {
      const { container } = render(<IdentityPage />)
      const form = container.querySelector('form')
      expect(form).toBeInTheDocument()
    })
  })
})
