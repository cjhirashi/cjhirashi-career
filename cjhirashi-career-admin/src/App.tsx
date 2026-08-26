import React, { Suspense } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Components
import { PrivateRoute } from '@/components/PrivateRoute'
import { Layout } from '@/components/Layout'
import { LoadingSpinner } from '@/components/LoadingSpinner'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Pages
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { MetricsPage } from '@/pages/MetricsPage'
import { ChangePasswordPage } from '@/pages/ChangePasswordPage'
import { ProfilePage } from '@/pages/ProfilePage'
import { CareerResourcePage } from '@/pages/CareerResourcePage'
import { FilesPage } from '@/pages/FilesPage'
import { LinkedInPage } from '@/pages/LinkedInPage'
import { AgentMetricsPage } from '@/pages/AgentMetricsPage'
import { AgentInstructionsPage } from '@/pages/AgentInstructionsPage'
import { AgentCatalogPage } from '@/pages/AgentCatalogPage'
import { AdminSectionsPage, AdminSectionDetailPage } from '@/pages/AdminSectionsPage'
import { AgentToolsPage } from '@/pages/AgentToolsPage'
import { AgentMemoryPage } from '@/pages/AgentMemoryPage'
import { AgentAuditLogPage } from '@/pages/AgentAuditLogPage'
import { TasksPage } from '@/pages/TasksPage'
import { AgentGeneralChatPage } from '@/pages/AgentGeneralChatPage'
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

export const App: React.FC = () => {
  return (
    <ErrorBoundary>
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
            path="/career/:resourceKey/:recordSlug?"
            element={
              <PrivateRoute>
                <Layout>
                  <CareerResourcePage />
                </Layout>
              </PrivateRoute>
            }
          />

          {/* Agent Bedrock administration - metrics, methodologies (reuses
              /career/operational-methodologies, not duplicated here),
              memory, instructions, and MCP tools. See Sidebar.tsx's
              "Agente IA" section. */}
          <Route
            path="/agent/chat"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentGeneralChatPage />
                </Layout>
              </PrivateRoute>
            }
          />
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
            path="/agent/metrics"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentMetricsPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/settings/agents/:profileId?"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentCatalogPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/settings/sections"
            element={
              <PrivateRoute>
                <Layout>
                  <AdminSectionsPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/settings/sections/:sectionId"
            element={
              <PrivateRoute>
                <Layout>
                  <AdminSectionDetailPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route path="/agent/catalog" element={<Navigate to="/settings/agents" replace />} />
          <Route path="/agent/catalog/:profileId" element={<LegacyAgentCatalogRedirect />} />
          <Route
            path="/agent/memory"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentMemoryPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/agent/instructions"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentInstructionsPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/agent/tools"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentToolsPage />
                </Layout>
              </PrivateRoute>
            }
          />
          <Route
            path="/agent/audit-log"
            element={
              <PrivateRoute>
                <Layout>
                  <AgentAuditLogPage />
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

const LegacyAgentCatalogRedirect: React.FC = () => {
  const { profileId } = useParams()
  return <Navigate to={`/settings/agents/${profileId}`} replace />
}

export default App
