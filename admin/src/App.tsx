import React, { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Components
import { PrivateRoute } from '@/components/PrivateRoute'
import { Layout } from '@/components/Layout'
import { LoadingSpinner } from '@/components/LoadingSpinner'

// Pages
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { MetricsPage } from '@/pages/MetricsPage'
import { ChangePasswordPage } from '@/pages/ChangePasswordPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { CareerResourcePage } from '@/pages/CareerResourcePage'
import { FilesPage } from '@/pages/FilesPage'
import { LinkedInPage } from '@/pages/LinkedInPage'

// Lazy: the only page that pulls in recharts (~100kB gzipped) - loading it
// eagerly like the rest would add that weight to every page's first load,
// not just this one.
const SearchMetricsPage = React.lazy(() =>
  import('@/pages/SearchMetricsPage').then((m) => ({ default: m.SearchMetricsPage }))
)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 10,
    },
  },
})

export const App: React.FC = () => {
  return (
    <QueryClientProvider client={queryClient}>
      <Router>
        <Routes>
          {/* Login - No layout */}
          <Route path="/login" element={<LoginPage />} />

          {/* Protected routes - With layout */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <Layout>
                  <DashboardPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/metrics"
            element={
              <PrivateRoute>
                <Layout>
                  <MetricsPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/search-metrics"
            element={
              <PrivateRoute>
                <Layout>
                  <Suspense fallback={<LoadingSpinner fullScreen={false} message="Cargando métricas..." />}>
                    <SearchMetricsPage />
                  </Suspense>
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/files"
            element={
              <PrivateRoute>
                <Layout>
                  <FilesPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/linkedin"
            element={
              <PrivateRoute>
                <Layout>
                  <LinkedInPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/profile"
            element={
              <PrivateRoute>
                <Layout>
                  <ProfilePage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/change-password"
            element={
              <PrivateRoute>
                <Layout>
                  <ChangePasswordPage />
                </Layout>
              </PrivateRoute>
            }
          />

          {/* Career domain (v2) - generic route shared by all 30 resources,
              see src/config/careerResources.ts for the registry. */}
          <Route
            path="/career/:resourceKey"
            element={
              <PrivateRoute>
                <Layout>
                  <CareerResourcePage />
                </Layout>
              </PrivateRoute>
            }
          />

          {/* Fallback - redirect to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
  )
}

export default App
