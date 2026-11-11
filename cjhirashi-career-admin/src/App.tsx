import React, { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Components
import { PrivateRoute } from '@/components/PrivateRoute'
import { Layout } from '@/components/Layout'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { usePageTitle } from '@/hooks/usePageTitle'

// Pages
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { MetricsPage } from '@/pages/MetricsPage'
import { PortalSettingsPage } from '@/pages/PortalSettingsPage'
import { ChangePasswordPage } from '@/pages/ChangePasswordPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { CareerResourcePage } from '@/pages/CareerResourcePage'
import { FilesPage } from '@/pages/FilesPage'
import { ErrorReportsPage, ErrorReportDetailPage } from '@/pages/ErrorReportsPage'
import { TasksPage } from '@/pages/TasksPage'
import { AgentPdfTemplatesPage } from '@/pages/AgentPdfTemplatesPage'
import { AgentPdfTemplateStylesPage } from '@/pages/AgentPdfTemplateStylesPage'

// Lazy: the only page that pulls in recharts (~100kB gzipped) - loading it
// eagerly like the rest would add that weight to every page's first load,
// not just this one.
const SearchMetricsPage = React.lazy(() =>
  import('@/pages/SearchMetricsPage').then((m) => ({ default: m.SearchMetricsPage }))
)
const JobDiscoveryPage = React.lazy(() =>
  import('@/pages/JobDiscoveryPage').then((m) => ({ default: m.JobDiscoveryPage }))
)

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5,
      gcTime: 1000 * 60 * 10,
    },
  },
})

/** Lives inside <Router> (needs routing context) but outside <Routes>, so it
 * tracks every navigation - including /login and the catch-all redirect -
 * without duplicating a hook call into Layout and LoginPage separately. */
const PageTitleManager: React.FC = () => {
  usePageTitle()
  return null
}

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <Router>
        <PageTitleManager />
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
            path="/metrics/settings"
            element={
              <PrivateRoute>
                <Layout>
                  <PortalSettingsPage />
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
            path="/job-discovery"
            element={
              <PrivateRoute>
                <Layout>
                  <Suspense fallback={<LoadingSpinner fullScreen={false} message="Cargando descubrimiento..." />}>
                    <JobDiscoveryPage />
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
            path="/tasks"
            element={
              <PrivateRoute>
                <Layout>
                  <TasksPage />
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
            path="/career/:resourceKey/:recordSlug?"
            element={
              <PrivateRoute>
                <Layout>
                  <CareerResourcePage />
                </Layout>
              </PrivateRoute>
            }
          />

          {/* PDF templates and styles */}
          <Route
            path="/agent/pdf-templates/:recordSlug?"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentPdfTemplatesPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/agent/pdf-template-styles/:recordSlug?"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentPdfTemplateStylesPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/settings/error-reports"
            element={
              <PrivateRoute>
                <Layout>
                  <ErrorReportsPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/settings/error-reports/:reportId"
            element={
              <PrivateRoute>
                <Layout>
                  <ErrorReportDetailPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route path="/agent/tasks" element={<Navigate to="/tasks" replace />} />

          {/* Fallback - redirect to dashboard */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </Router>
    </QueryClientProvider>
    </ErrorBoundary>
  )
}

export default App
