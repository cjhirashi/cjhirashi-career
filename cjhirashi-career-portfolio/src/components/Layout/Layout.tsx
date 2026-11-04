import { ReactNode } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'
import { useCaptureOwnerToken, useTrackLinks, useTrackPageview, useTrackWebVitals } from '@/hooks/useTracking'

interface LayoutProps {
  children: ReactNode
}

export const Layout = ({ children }: LayoutProps) => {
  // El orden importa: el token del dueño se guarda antes del primer pageview.
  useCaptureOwnerToken()
  useTrackPageview()
  useTrackLinks()
  useTrackWebVitals()

  return (
    <div className="flex flex-col min-h-screen bg-bg text-text overflow-x-hidden">
      <Header />
      <main className="flex-grow">{children}</main>
      <Footer />
    </div>
  )
}
