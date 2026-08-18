import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClientProvider, QueryClient } from '@tanstack/react-query'

// Components
import { PrivateRoute } from '@/components/PrivateRoute'
import { Layout } from '@/components/Layout'

// Pages
import { LoginPage } from '@/pages/LoginPage'
import { DashboardPage } from '@/pages/DashboardPage'
import { IdentityPage } from '@/pages/IdentityPage'
import { CompetenciesPage } from '@/pages/CompetenciesPage'
import { EvidencePage } from '@/pages/EvidencePage'
import { JobStrategiesPage } from '@/pages/JobStrategiesPage'
import { NetworkingPage } from '@/pages/NetworkingPage'
import { InterviewsPage } from '@/pages/InterviewsPage'
import { MetricsPage } from '@/pages/MetricsPage'
import { ChangePasswordPage } from '@/pages/ChangePasswordPage'
import { CareerResourcePage } from '@/pages/CareerResourcePage'

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
            path="/identity"
            element={
              <PrivateRoute>
                <Layout>
                  <IdentityPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/competencies"
            element={
              <PrivateRoute>
                <Layout>
                  <CompetenciesPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/evidence"
            element={
              <PrivateRoute>
                <Layout>
                  <EvidencePage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/job-strategies"
            element={
              <PrivateRoute>
                <Layout>
                  <JobStrategiesPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/networking"
            element={
              <PrivateRoute>
                <Layout>
                  <NetworkingPage />
                </Layout>
              </PrivateRoute>
            }
          />

          <Route
            path="/interviews"
            element={
              <PrivateRoute>
                <Layout>
                  <InterviewsPage />
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
