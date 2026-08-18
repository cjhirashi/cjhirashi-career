import React from 'react'

export const EvidencePage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Evidence</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">
          Document your projects, positions, achievements, and STAR cases
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {['Projects', 'Positions', 'Achievements', 'STAR Cases'].map((item) => (
          <div key={item} className="card">
            <div className="card-body text-center py-8">
              <p className="text-lg font-semibold text-slate-900 dark:text-slate-100">{item}</p>
              <p className="text-slate-600 dark:text-slate-400 text-sm mt-2">Coming soon</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
