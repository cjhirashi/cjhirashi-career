import React from 'react'
import { JsonListConfig } from '@/config/careerResources'
import { isJsonListEmpty, jsonListConfigOf, toEditorRows } from './jsonListUtils'

interface JsonListViewProps {
  value: unknown
  jsonList?: JsonListConfig
}

/**
 * Read-only rendering of a JSONB list field: definition list, bullets, or
 * labeled record cards — never a JSON dump.
 */
export const JsonListView: React.FC<JsonListViewProps> = ({ value, jsonList }) => {
  const config = jsonListConfigOf(jsonList)
  if (isJsonListEmpty(value)) {
    return <span className="text-text-muted">—</span>
  }

  const rows = toEditorRows(value, config)

  if (config.kind === 'kv') {
    return (
      <dl className="json-list-view-kv">
        {rows.map((row, index) => (
          <div key={`${row.name}-${index}`} className="json-list-view-kv-row">
            <dt>{row.name?.trim() || `Dato ${index + 1}`}</dt>
            <dd>{row.value?.trim() || '—'}</dd>
          </div>
        ))}
      </dl>
    )
  }

  if (config.kind === 'text') {
    return (
      <ul className="json-list-view-text">
        {rows.map((row, index) => (
          <li key={`${row.text}-${index}`}>{row.text}</li>
        ))}
      </ul>
    )
  }

  const fields = config.itemFields ?? []
  return (
    <ul className="json-list-view-records">
      {rows.map((row, index) => {
        const titleField = fields[0]
        const title = titleField ? row[titleField.name]?.trim() : ''
        return (
          <li key={index} className="json-list-view-record">
            <p className="json-list-view-record-title">
              {title || `${config.itemNoun} ${index + 1}`}
            </p>
            <dl>
              {fields
                .filter((field) => field !== titleField)
                .map((field) => {
                  const cell = row[field.name]?.trim()
                  if (!cell) return null
                  return (
                    <div key={field.name} className="json-list-view-kv-row">
                      <dt>{field.label}</dt>
                      <dd>{cell}</dd>
                    </div>
                  )
                })}
            </dl>
          </li>
        )
      })}
    </ul>
  )
}
