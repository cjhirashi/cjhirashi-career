import { ReactNode } from 'react'
import { Header } from './Header'
import { Footer } from './Footer'
import { useTrackPageview } from '@/hooks/useTracking'

interface LayoutProps {
  children: ReactNode
}

export const Layout = ({ children }: LayoutProps) => {
  useTrackPageview()

  return (
    <div className="flex flex-col min-h-screen bg-bg text-text overflow-x-hidden">
      <Header />
      <main className="flex-grow">{children}</main>
      <Footer />
    </div>
  )
}
