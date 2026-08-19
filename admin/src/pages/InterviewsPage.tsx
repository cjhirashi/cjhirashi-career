import React from 'react'
import { MessageCircle, Laptop, BookOpen } from 'lucide-react'

export const InterviewsPage: React.FC = () => {
  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900 dark:text-slate-100">Interview Preparation</h1>
        <p className="text-slate-600 dark:text-slate-400 mt-2">
          Prepare for interviews with questions and answers
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-slate-900 dark:text-slate-100">Behavioral</h2>
          </div>
          <div className="card-body text-center py-8">
            <MessageCircle size={28} className="mx-auto mb-2 text-primary" aria-hidden="true" />
            <p className="text-slate-600 dark:text-slate-400">Coming soon</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-slate-900 dark:text-slate-100">Technical</h2>
          </div>
          <div className="card-body text-center py-8">
            <Laptop size={28} className="mx-auto mb-2 text-primary" aria-hidden="true" />
            <p className="text-slate-600 dark:text-slate-400">Coming soon</p>
          </div>
        </div>

        <div className="card">
          <div className="card-header">
            <h2 className="font-semibold text-slate-900 dark:text-slate-100">Domain</h2>
          </div>
          <div className="card-body text-center py-8">
            <BookOpen size={28} className="mx-auto mb-2 text-primary" aria-hidden="true" />
            <p className="text-slate-600 dark:text-slate-400">Coming soon</p>
          </div>
        </div>
      </div>
    </div>
  )
}
