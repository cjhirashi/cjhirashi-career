import React from 'react'
import { CareerResourceView } from '@/components/career/CareerResourceView'
import { pdfTemplateStylesConfig } from '@/config/careerResources'

export const AgentPdfTemplateStylesPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Estilos PDF</h1>
        <p className="text-text-secondary mt-2">
          Define estilos CSS reutilizables para plantillas PDF. Documenta clases y etiquetas en la guía de estilo para
          saber qué elementos puedes usar al diseñar plantillas HTML.
        </p>
      </div>

      <CareerResourceView
        config={pdfTemplateStylesConfig}
        apiMode="pdf-template-styles"
        listPath="/agent/pdf-template-styles"
      />
    </div>
  )
}
