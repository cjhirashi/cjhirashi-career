import React from 'react'
import { CareerResourceView } from '@/components/career/CareerResourceView'
import { pdfTemplateStylesConfig } from '@/config/careerResources'

export const AgentPdfTemplateStylesPage: React.FC = () => {
  return (
    <CareerResourceView
      config={pdfTemplateStylesConfig}
      apiMode="pdf-template-styles"
      listPath="/agent/pdf-template-styles"
    />
  )
}
