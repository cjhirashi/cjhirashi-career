import React from 'react'

export const MetricsPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Metrics</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">Monitor your portfolio progress and activity</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Profile Completeness</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">0%</p>
            </div>
            <div className="text-3xl">📊</div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Portal Views</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">0</p>
            </div>
            <div className="text-3xl">👁️</div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Interactions</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">0</p>
            </div>
            <div className="text-3xl">🔗</div>
          </div>
        </div>

        <div className="card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-slate-600 dark:text-slate-400 text-sm font-medium">Agent Activity</p>
              <p className="text-3xl font-bold text-slate-900 dark:text-slate-100 mt-2">0</p>
            </div>
            <div className="text-3xl">🤖</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-header">
          <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-100">Activity Timeline</h2>
        </div>
        <div className="card-body text-center py-8">
          <p className="text-slate-600 dark:text-slate-400">Real-time metrics coming soon</p>
        </div>
      </div>
    </div>
  )
}
