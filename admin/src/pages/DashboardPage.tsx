import React from 'react'
import { useAuth } from '@/hooks/useAuth'

export const DashboardPage: React.FC = () => {
  const { user } = useAuth()

  return (
    <div>
      {/* Page Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-slate-600 mt-2">Welcome back, {user?.full_name}!</p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Total Skills</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">0</p>
            </div>
            <div className="text-3xl">🎯</div>
          </div>
          <p className="text-slate-500 text-xs mt-4">Add your competencies</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Projects</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">0</p>
            </div>
            <div className="text-3xl">📁</div>
          </div>
          <p className="text-slate-500 text-xs mt-4">Showcase your work</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Positions</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">0</p>
            </div>
            <div className="text-3xl">💼</div>
          </div>
          <p className="text-slate-500 text-xs mt-4">Document your experience</p>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 text-sm font-medium">Contacts</p>
              <p className="text-3xl font-bold text-slate-900 mt-2">0</p>
            </div>
            <div className="text-3xl">🤝</div>
          </div>
          <p className="text-slate-500 text-xs mt-4">Build your network</p>
        </div>
      </div>

      {/* Getting Started */}
      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-slate-900">Getting Started</h2>
        </div>
        <div className="card-body">
          <div className="space-y-4">
            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 rounded-full flex items-center justify-center text-cyan-700 font-semibold">
                1
              </div>
              <div>
                <h3 className="font-medium text-slate-900">Set Your Professional Identity</h3>
                <p className="text-slate-600 text-sm mt-1">
                  Define your IKIGAI, differentiators, and professional narrative
                </p>
                <a href="/identity" className="text-cyan-600 hover:text-cyan-700 text-sm font-medium mt-2 inline-block">
                  Go to Identity →
                </a>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 rounded-full flex items-center justify-center text-cyan-700 font-semibold">
                2
              </div>
              <div>
                <h3 className="font-medium text-slate-900">Document Your Competencies</h3>
                <p className="text-slate-600 text-sm mt-1">
                  Add technical, transferable, and business skills with proficiency levels
                </p>
                <a href="/competencies" className="text-cyan-600 hover:text-cyan-700 text-sm font-medium mt-2 inline-block">
                  Go to Competencies →
                </a>
              </div>
            </div>

            <div className="flex items-start space-x-4">
              <div className="flex-shrink-0 w-8 h-8 bg-cyan-100 rounded-full flex items-center justify-center text-cyan-700 font-semibold">
                3
              </div>
              <div>
                <h3 className="font-medium text-slate-900">Showcase Your Evidence</h3>
                <p className="text-slate-600 text-sm mt-1">
                  Add projects, positions, achievements, and STAR cases
                </p>
                <a href="/evidence" className="text-cyan-600 hover:text-cyan-700 text-sm font-medium mt-2 inline-block">
                  Go to Evidence →
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
