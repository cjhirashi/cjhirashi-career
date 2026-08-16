import React from 'react'

export const NetworkingPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Networking</h1>
        <p className="text-slate-600 mt-2">
          Manage your professional contacts and opportunities
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-slate-900">Contacts</h2>
          </div>
          <div className="card-body text-center py-8">
            <p className="text-slate-600">Coming soon</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-slate-900">Opportunities</h2>
          </div>
          <div className="card-body text-center py-8">
            <p className="text-slate-600">Coming soon</p>
          </div>
        </div>
      </div>
    </div>
  )
}
