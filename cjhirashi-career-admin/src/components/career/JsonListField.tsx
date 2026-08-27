import React from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { JsonListConfig, JsonListItemField } from '@/config/careerResources'
import {
  JsonListRow,
  blankJsonListRow,
  jsonListConfigOf,
  parseEditorRows,
} from './jsonListUtils'

interface JsonListFieldProps {
  id: string
  value: string
  onChange: (value: string) => void
  jsonList?: JsonListConfig
  disabled?: boolean
}

const emit = (rows: JsonListRow[], onChange: (value: string) => void) => {
  onChange(JSON.stringify(rows))
}

const ItemIndex = ({ index }: { index: number }) => (
  <span className="json-list-index" aria-hidden="true">
    {String(index + 1).padStart(2, '0')}
  </span>
)

const RemoveButton = ({ label, onClick, disabled }: { label: string; onClick: () => void; disabled?: boolean }) => (
  <button
    type="button"
    className="json-list-remove"
    aria-label={label}
    onClick={onClick}
    disabled={disabled}
  >
    <Trash2 size={14} />
  </button>
)

const RecordInput = ({
  id,
  field,
  value,
  onChange,
  disabled,
}: {
  id: string
  field: JsonListItemField
  value: string
  onChange: (value: string) => void
  disabled?: boolean
}) => {
  const inputType = field.type === 'url' ? 'url' : field.type === 'date' ? 'date' : 'text'
  const common = {
    id,
    value,
    disabled,
    placeholder: field.placeholder,
    onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(e.target.value),
    className: 'input-field',
  }

  return (
    <div className={field.wide ? 'json-list-field json-list-field-wide' : 'json-list-field'}>
      <label htmlFor={id} className="json-list-field-label">
        {field.label}
      </label>
      {field.type === 'textarea' ? (
        <textarea {...common} rows={2} />
      ) : (
        <input {...common} type={inputType} />
      )}
    </div>
  )
}

/**
 * List editor for JSONB career fields. Stores editor rows as a JSON array
 * string in form state; `fromFormValue` turns that into the API shape.
 */
export const JsonListField: React.FC<JsonListFieldProps> = ({
  id,
  value,
  onChange,
  jsonList,
  disabled,
}) => {
  const config = jsonListConfigOf(jsonList)
  const rows = parseEditorRows(value, config)
  const noun = config.itemNoun
  const addLabel = config.addLabel ?? `Añadir ${noun}`

  const setRow = (index: number, patch: JsonListRow) => {
    emit(
      rows.map((row, i) => (i === index ? { ...row, ...patch } : row)),
      onChange
    )
  }

  const removeRow = (index: number) => {
    emit(
      rows.filter((_, i) => i !== index),
      onChange
    )
  }

  const addRow = () => {
    emit([...rows, blankJsonListRow(config)], onChange)
  }

  return (
    <div className="json-list" id={id}>
      {rows.length === 0 && (
        <p className="json-list-empty">Aún no hay registros. Añade el primero.</p>
      )}

      <ul className="json-list-items">
        {rows.map((row, index) => (
          <li key={`${id}-${index}`} className="json-list-item">
            <div className="json-list-item-head">
              <ItemIndex index={index} />
              <span className="json-list-item-title">
                {noun.charAt(0).toUpperCase() + noun.slice(1)} {index + 1}
              </span>
              <RemoveButton
                label={`Quitar ${noun} ${index + 1}`}
                onClick={() => removeRow(index)}
                disabled={disabled}
              />
            </div>

            {config.kind === 'kv' && (
              <div className="json-list-grid">
                <div className="json-list-field">
                  <label htmlFor={`${id}-${index}-name`} className="json-list-field-label">
                    {config.keyLabel ?? 'Nombre'}
                  </label>
                  <input
                    id={`${id}-${index}-name`}
                    className="input-field"
                    value={row.name ?? ''}
                    disabled={disabled}
                    placeholder={config.keyPlaceholder ?? 'Ej. Equipo gestionado'}
                    onChange={(e) => setRow(index, { name: e.target.value })}
                  />
                </div>
                <div className="json-list-field json-list-field-wide">
                  <label htmlFor={`${id}-${index}-value`} className="json-list-field-label">
                    {config.valueLabel ?? 'Valor'}
                  </label>
                  <textarea
                    id={`${id}-${index}-value`}
                    className="input-field"
                    rows={2}
                    value={row.value ?? ''}
                    disabled={disabled}
                    placeholder={config.valuePlaceholder ?? 'Dato o cifra'}
                    onChange={(e) => setRow(index, { value: e.target.value })}
                  />
                </div>
              </div>
            )}

            {config.kind === 'text' && (
              <div className="json-list-grid">
                <div className="json-list-field json-list-field-wide">
                  <label htmlFor={`${id}-${index}-text`} className="sr-only">
                    {noun} {index + 1}
                  </label>
                  <input
                    id={`${id}-${index}-text`}
                    className="input-field"
                    value={row.text ?? ''}
                    disabled={disabled}
                    placeholder={config.textPlaceholder ?? `Escribe el ${noun}`}
                    onChange={(e) => setRow(index, { text: e.target.value })}
                  />
                </div>
              </div>
            )}

            {config.kind === 'records' && (
              <div className="json-list-grid">
                {(config.itemFields ?? []).map((field) => (
                  <RecordInput
                    key={field.name}
                    id={`${id}-${index}-${field.name}`}
                    field={field}
                    value={row[field.name] ?? ''}
                    disabled={disabled}
                    onChange={(next) => setRow(index, { [field.name]: next })}
                  />
                ))}
              </div>
            )}
          </li>
        ))}
      </ul>

      <button type="button" className="json-list-add" onClick={addRow} disabled={disabled}>
        <Plus size={16} aria-hidden="true" />
        {addLabel}
      </button>
    </div>
  )
}
