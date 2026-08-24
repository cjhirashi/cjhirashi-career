import React from 'react'
import { CareerResourceView } from '@/components/career/CareerResourceView'
import { pdfOutputTemplatesConfig } from '@/config/careerResources'

export const AgentPdfTemplatesPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text">Plantillas PDF</h1>
        <p className="text-text-secondary mt-2">
          Diseña plantillas HTML/CSS para CVs y cartas. El agente pdf_design y el generador PDF las usan vía{' '}
          <code className="text-xs">template_id</code>.
        </p>
      </div>

      <CareerResourceView config={pdfOutputTemplatesConfig} apiMode="pdf-templates" />
    </div>
  )
}
