import React, { useMemo, useState } from 'react'
import { FieldConfig, ResourceConfig } from '@/config/careerResources'
import { fromFormValue, FieldParseError, toFormValue } from './careerFieldUtils'
import { FkSelectField } from './FkSelectField'

interface ResourceFormProps {
  config: ResourceConfig
  /** Existing record when editing, or undefined/empty object when creating. */
  initialValues?: Record<string, unknown>
  /**
   * Fixed values (typically a foreign key to a parent row in a nested view)
   * that are merged into the payload but not shown as editable fields.
   */
  presetValues?: Record<string, unknown>
  onSubmit: (payload: Record<string, unknown>) => void
  onCancel?: () => void
  isSubmitting?: boolean
  submitLabel?: string
  layout?: 'grid' | 'stacked'
}

type FormState = Record<string, string | boolean>

const buildInitialState = (fields: FieldConfig[], initialValues?: Record<string, unknown>): FormState => {
  const state: FormState = {}
  fields.forEach((field) => {
    state[field.name] = toFormValue(field.type, initialValues?.[field.name])
  })
  return state
}

export const ResourceForm: React.FC<ResourceFormProps> = ({
  config,
  initialValues,
  presetValues,
  onSubmit,
  onCancel,
  isSubmitting = false,
  submitLabel = 'Guardar',
  layout = 'grid',
}) => {
  const visibleFields = useMemo(
    () => config.fields.filter((f) => !presetValues || !(f.name in presetValues)),
    [config.fields, presetValues]
  )

  const [values, setValues] = useState<FormState>(() => buildInitialState(visibleFields, initialValues))
  const [error, setError] = useState<string | null>(null)

  const handleChange = (name: string, value: string | boolean) => {
    setValues((prev) => ({ ...prev, [name]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)

    const payload: Record<string, unknown> = { ...(presetValues || {}) }
    try {
      for (const field of visibleFields) {
        payload[field.name] = fromFormValue(field, values[field.name])
      }
    } catch (err) {
      if (err instanceof FieldParseError) {
        setError(err.message)
        return
      }
      setError('Error al procesar el formulario')
      return
    }

    onSubmit(payload)
  }

  const renderField = (field: FieldConfig) => {
    const value = values[field.name]
    const commonProps = {
      id: `field-${config.key}-${field.name}`,
      name: field.name,
    }

    switch (field.type) {
      case 'boolean':
        return (
          <label
            key={field.name}
            className="flex items-center gap-2 mt-6"
            htmlFor={commonProps.id}
          >
            <input
              {...commonProps}
              type="checkbox"
              checked={Boolean(value)}
              onChange={(e) => handleChange(field.name, e.target.checked)}
              className="h-4 w-4 rounded border-border text-cyan-600 focus:ring-cyan-500"
            />
            <span className="text-sm text-text">{field.label}</span>
          </label>
        )
      case 'fk-select':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <FkSelectField
              id={commonProps.id}
              name={commonProps.name}
              fkResource={field.fkResource ?? ''}
              fkLabelField={field.fkLabelField}
              value={typeof value === 'string' ? value : ''}
              onChange={(v) => handleChange(field.name, v)}
              required={field.required}
              placeholder={field.placeholder}
            />
            {field.helpText && <p className="text-text-secondary text-xs mt-1">{field.helpText}</p>}
          </div>
        )
      case 'select':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <select
              {...commonProps}
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              className="input-field"
            >
              <option value="">-- Selecciona --</option>
              {field.options?.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>
        )
      case 'textarea':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <textarea
              {...commonProps}
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              placeholder={field.placeholder}
              className="input-field h-48 font-mono text-xs"
            />
            <p className="text-text-secondary text-xs mt-1">
              Admite Markdown - deja una línea en blanco entre párrafos, **negritas**, listas con &quot;- &quot;...
            </p>
            {field.helpText && <p className="text-text-secondary text-xs mt-1">{field.helpText}</p>}
          </div>
        )
      case 'json':
      case 'string-array':
      case 'number-array':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <textarea
              {...commonProps}
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              placeholder={field.placeholder}
              className="input-field h-24 font-mono text-xs"
            />
            {field.helpText && <p className="text-text-secondary text-xs mt-1">{field.helpText}</p>}
          </div>
        )
      case 'date':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <input
              {...commonProps}
              type="date"
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              className="input-field"
            />
          </div>
        )
      case 'datetime':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <input
              {...commonProps}
              type="datetime-local"
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              className="input-field"
            />
          </div>
        )
      case 'number':
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <input
              {...commonProps}
              type="number"
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              placeholder={field.placeholder}
              className="input-field"
            />
          </div>
        )
      case 'text':
      default:
        return (
          <div key={field.name} className="form-group">
            <label htmlFor={commonProps.id} className="form-label">
              {field.label}
              {field.required && <span className="text-red-500"> *</span>}
            </label>
            <input
              {...commonProps}
              type="text"
              value={typeof value === 'string' ? value : ''}
              onChange={(e) => handleChange(field.name, e.target.value)}
              required={field.required}
              placeholder={field.placeholder}
              className="input-field"
            />
          </div>
        )
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" aria-label={`Formulario de ${config.labelSingular}`}>
      {error && (
        <div className="p-3 bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/50 rounded-lg">
          <p className="text-red-800 dark:text-red-300 text-sm font-medium">{error}</p>
        </div>
      )}

      <div className={layout === 'grid' ? 'grid grid-cols-1 md:grid-cols-2 gap-4' : 'space-y-4'}>
        {visibleFields.map((field) => (
          <div key={field.name} className={field.fullWidth && layout === 'grid' ? 'md:col-span-2' : ''}>
            {renderField(field)}
          </div>
        ))}
      </div>

      <div className="flex justify-end gap-3 pt-2">
        {onCancel && (
          <button type="button" onClick={onCancel} className="btn-secondary" disabled={isSubmitting}>
            Cancelar
          </button>
        )}
        <button type="submit" className="btn-primary" disabled={isSubmitting}>
          {isSubmitting ? 'Guardando...' : submitLabel}
        </button>
      </div>
    </form>
  )
}
