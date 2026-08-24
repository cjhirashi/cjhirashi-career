import React, { useEffect, useState } from 'react'
import { FileText, Plus, Save, Trash2, Download } from 'lucide-react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { pdfTemplatesApi, PdfOutputTemplate, PdfTemplatePayload } from '@/api/pdfTemplates'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { getErrorMessage } from '@/utils/errors'

const EMPTY_FORM: PdfTemplatePayload = {
  slug: '',
  document_type: 'cv',
  title: '',
  description: '',
  html_template: '<h1>{{title}}</h1>\n<div>{{content}}</div>',
  css_content: 'h1 { color: #0891B2; }',
  is_default: false,
  is_active: true,
}

export const AgentPdfTemplatesPage: React.FC = () => {
  const queryClient = useQueryClient()
  const { data: templates = [], isLoading, isError, error } = useQuery({
    queryKey: ['pdf-templates'],
    queryFn: () => pdfTemplatesApi.list(),
    refetchOnWindowFocus: true,
    staleTime: 0,
  })

  const [selectedId, setSelectedId] = useState<string | 'new' | null>(null)
  const [form, setForm] = useState<PdfTemplatePayload>(EMPTY_FORM)
  const [formError, setFormError] = useState<string | null>(null)

  const selected = templates.find((t) => t.id === selectedId)

  useEffect(() => {
    if (selectedId === 'new') {
      setForm(EMPTY_FORM)
      return
    }
    if (selected) {
      setForm({
        slug: selected.slug,
        document_type: selected.document_type,
        title: selected.title,
        description: selected.description ?? '',
        html_template: selected.html_template,
        css_content: selected.css_content ?? '',
        is_default: selected.is_default,
        is_active: selected.is_active,
      })
    }
  }, [selectedId, selected])

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['pdf-templates'] })

  const saveMutation = useMutation({
    mutationFn: async () => {
      if (selectedId === 'new') return pdfTemplatesApi.create(form)
      if (typeof selectedId === 'string' && selectedId !== 'new') return pdfTemplatesApi.update(selectedId as string, form)
      throw new Error('Nada seleccionado')
    },
    onSuccess: (row) => {
      setFormError(null)
      invalidate()
      setSelectedId(row.id)
    },
    onError: (err) => setFormError(getErrorMessage(err)),
  })

  const deleteMutation = useMutation({
    mutationFn: (id: string) => pdfTemplatesApi.remove(id),
    onSuccess: () => {
      invalidate()
      setSelectedId(null)
    },
  })

  const previewMutation = useMutation({
    mutationFn: async (id: string) => {
      const blob = await pdfTemplatesApi.render(id, {
        title: 'Vista previa',
        content: 'Contenido de ejemplo para la plantilla PDF.',
      })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank', 'noopener,noreferrer')
      setTimeout(() => URL.revokeObjectURL(url), 60_000)
    },
  })

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Plantillas PDF</h1>
        <p className="text-text-secondary mt-2">
          Diseña plantillas HTML/CSS para CVs y cartas. El agente pdf_design y el generador PDF las usan vía{' '}
          <code className="text-xs">template_id</code>.
        </p>
      </div>

      {isLoading && <LoadingSpinner fullScreen={false} message="Cargando plantillas..." />}
      {isError && <p className="text-red-600 dark:text-red-400 text-sm">{getErrorMessage(error)}</p>}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1">
          <div className="card-header flex items-center justify-between">
            <h2 className="text-base font-semibold text-text flex items-center gap-2">
              <FileText size={17} className="text-primary" />
              Plantillas
            </h2>
            <button
              type="button"
              className="btn-primary flex items-center gap-1 text-xs px-3 py-1.5"
              onClick={() => setSelectedId('new')}
            >
              <Plus size={14} />
              Nueva
            </button>
          </div>
          <div className="card-body space-y-1">
            {templates.length === 0 && (
              <p className="text-text-secondary text-sm text-center py-4">Sin plantillas todavía.</p>
            )}
            {templates.map((t: PdfOutputTemplate) => (
              <button
                key={t.id}
                type="button"
                onClick={() => setSelectedId(t.id)}
                className={`w-full text-left px-3 py-2 rounded-xl text-sm transition-colors ${
                  selectedId === t.id ? 'bg-primary/15 text-text' : 'hover:bg-glass text-text-secondary'
                }`}
              >
                <span className="font-medium text-text">{t.title}</span>
                <span className="block text-xs text-text-muted">
                  {t.document_type} · {t.slug}
                  {t.is_default ? ' · default' : ''}
                </span>
              </button>
            ))}
          </div>
        </div>

        <div className="card lg:col-span-2">
          <div className="card-header">
            <h2 className="text-base font-semibold text-text">
              {selectedId === 'new' ? 'Nueva plantilla' : selected ? `Editar: ${selected.title}` : 'Selecciona una plantilla'}
            </h2>
          </div>
          <div className="card-body space-y-3">
            {selectedId === null ? (
              <p className="text-text-secondary text-sm text-center py-8">Elige una plantilla o crea una nueva.</p>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm font-medium text-text mb-1" htmlFor="pdf-template-slug">
                      Slug
                    </label>
                    <input
                      id="pdf-template-slug"
                      className="input-field text-sm"
                      placeholder="ej. cv-moderno"
                      value={form.slug}
                      onChange={(e) => setForm({ ...form, slug: e.target.value })}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-text mb-1" htmlFor="pdf-template-type">
                      Tipo de documento
                    </label>
                    <select
                      id="pdf-template-type"
                      className="input-field text-sm"
                      value={form.document_type}
                      onChange={(e) => setForm({ ...form, document_type: e.target.value })}
                    >
                      <option value="cv">cv</option>
                      <option value="cover-letter">cover-letter</option>
                      <option value="generic">generic</option>
                    </select>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-text mb-1" htmlFor="pdf-template-title">
                      Título
                    </label>
                    <input
                      id="pdf-template-title"
                      className="input-field text-sm"
                      placeholder="Nombre visible de la plantilla"
                      value={form.title}
                      onChange={(e) => setForm({ ...form, title: e.target.value })}
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-sm font-medium text-text mb-1" htmlFor="pdf-template-description">
                      Descripción
                    </label>
                    <input
                      id="pdf-template-description"
                      className="input-field text-sm"
                      placeholder="Uso previsto (opcional)"
                      value={form.description ?? ''}
                      onChange={(e) => setForm({ ...form, description: e.target.value })}
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-text mb-1" htmlFor="pdf-template-html">
                    Plantilla HTML
                  </label>
                  <textarea
                    id="pdf-template-html"
                    className="input-field text-sm font-mono"
                    rows={8}
                    placeholder="HTML con variables {{title}}, {{content}}, etc."
                    value={form.html_template}
                    onChange={(e) => setForm({ ...form, html_template: e.target.value })}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-text mb-1" htmlFor="pdf-template-css">
                    CSS
                  </label>
                  <textarea
                    id="pdf-template-css"
                    className="input-field text-sm font-mono"
                    rows={4}
                    placeholder="Estilos WeasyPrint (opcional)"
                    value={form.css_content ?? ''}
                    onChange={(e) => setForm({ ...form, css_content: e.target.value })}
                  />
                </div>
                <label className="flex items-center gap-2 text-sm text-text-secondary">
                  <input
                    type="checkbox"
                    checked={form.is_default ?? false}
                    onChange={(e) => setForm({ ...form, is_default: e.target.checked })}
                  />
                  Plantilla predeterminada para este tipo
                </label>
                {formError && <p className="text-red-600 dark:text-red-400 text-xs">{formError}</p>}
                <div className="flex flex-wrap gap-2">
                  <button
                    type="button"
                    className="btn-primary flex items-center gap-2 disabled:opacity-50"
                    disabled={saveMutation.isPending || !form.slug.trim() || !form.title.trim()}
                    onClick={() => saveMutation.mutate()}
                  >
                    <Save size={15} />
                    Guardar
                  </button>
                  {typeof selectedId === 'string' && selectedId !== 'new' && (
                    <>
                      <button
                        type="button"
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm border border-border hover:bg-glass"
                        disabled={previewMutation.isPending}
                        onClick={() => previewMutation.mutate(selectedId)}
                      >
                        <Download size={15} />
                        Vista previa PDF
                      </button>
                      <button
                        type="button"
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-sm text-red-600 hover:bg-red-500/10"
                        disabled={deleteMutation.isPending}
                        onClick={() => deleteMutation.mutate(selectedId)}
                      >
                        <Trash2 size={15} />
                        Eliminar
                      </button>
                    </>
                  )}
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
