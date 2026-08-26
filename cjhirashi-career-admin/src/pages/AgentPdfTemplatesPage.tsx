import React from 'react'
import { CareerResourceView } from '@/components/career/CareerResourceView'
import { pdfOutputTemplatesConfig } from '@/config/careerResources'

export const AgentPdfTemplatesPage: React.FC = () => {
  return (
    <CareerResourceView
      config={pdfOutputTemplatesConfig}
      apiMode="pdf-templates"
      listPath="/agent/pdf-templates"
    />
  )
}
