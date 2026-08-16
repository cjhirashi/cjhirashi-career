import React, { useState } from 'react'
import { Identity } from '@/types'

export const IdentityPage: React.FC = () => {
  const [formData, setFormData] = useState<Partial<Identity>>({
    ikigai_what_do_i_do: '',
    ikigai_what_do_i_love: '',
    ikigai_what_am_i_good_at: '',
    ikigai_what_pays: '',
    differentiators: [],
    professional_narrative: '',
    value_proposition: '',
  })

  const handleChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    console.log('Submit identity form:', formData)
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-slate-900">Professional Identity</h1>
        <p className="text-slate-600 mt-2">Define your professional identity and unique value</p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* IKIGAI Section */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-slate-900">Your IKIGAI</h2>
            <p className="text-slate-600 text-sm mt-1">
              Define what you do, love, are good at, and what pays
            </p>
          </div>
          <div className="card-body space-y-4">
            <div className="form-group">
              <label htmlFor="what_do_i_do" className="form-label">
                What do I do?
              </label>
              <textarea
                id="what_do_i_do"
                value={formData.ikigai_what_do_i_do || ''}
                onChange={(e) => handleChange('ikigai_what_do_i_do', e.target.value)}
                className="input-field h-24"
                placeholder="Describe your professional activities and responsibilities"
              />
            </div>

            <div className="form-group">
              <label htmlFor="what_do_i_love" className="form-label">
                What do I love?
              </label>
              <textarea
                id="what_do_i_love"
                value={formData.ikigai_what_do_i_love || ''}
                onChange={(e) => handleChange('ikigai_what_do_i_love', e.target.value)}
                className="input-field h-24"
                placeholder="What aspects of work bring you joy and fulfillment?"
              />
            </div>

            <div className="form-group">
              <label htmlFor="what_am_i_good_at" className="form-label">
                What am I good at?
              </label>
              <textarea
                id="what_am_i_good_at"
                value={formData.ikigai_what_am_i_good_at || ''}
                onChange={(e) => handleChange('ikigai_what_am_i_good_at', e.target.value)}
                className="input-field h-24"
                placeholder="List your strengths and expertise areas"
              />
            </div>

            <div className="form-group">
              <label htmlFor="what_pays" className="form-label">
                What pays?
              </label>
              <textarea
                id="what_pays"
                value={formData.ikigai_what_pays || ''}
                onChange={(e) => handleChange('ikigai_what_pays', e.target.value)}
                className="input-field h-24"
                placeholder="What market value do you have? What are people willing to pay for?"
              />
            </div>
          </div>
        </div>

        {/* Differentiators Section */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-slate-900">Key Differentiators</h2>
            <p className="text-slate-600 text-sm mt-1">
              What sets you apart from other professionals in your field?
            </p>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label htmlFor="differentiators" className="form-label">
                Your Top 3-5 Differentiators
              </label>
              <textarea
                id="differentiators"
                value={formData.differentiators?.join('\n') || ''}
                onChange={(e) =>
                  handleChange(
                    'differentiators',
                    e.target.value
                      .split('\n')
                      .filter((item) => item.trim())
                      .join(',')
                  )
                }
                className="input-field h-24"
                placeholder="Enter one differentiator per line&#10;Example: Deep expertise in cloud architecture&#10;Strong track record in scaling startups"
              />
              <p className="text-slate-500 text-xs mt-2">Enter one per line</p>
            </div>
          </div>
        </div>

        {/* Professional Narrative Section */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-slate-900">Professional Narrative</h2>
            <p className="text-slate-600 text-sm mt-1">
              Your elevator pitch - a compelling 2-3 minute introduction
            </p>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label htmlFor="narrative" className="form-label">
                Your Story
              </label>
              <textarea
                id="narrative"
                value={formData.professional_narrative || ''}
                onChange={(e) => handleChange('professional_narrative', e.target.value)}
                className="input-field h-32"
                placeholder="Tell your professional story in a compelling way. Include your journey, key achievements, and what drives you."
              />
              <p className="text-slate-500 text-xs mt-2">
                {(formData.professional_narrative || '').length} characters
              </p>
            </div>
          </div>
        </div>

        {/* Value Proposition Section */}
        <div className="card">
          <div className="card-header">
            <h2 className="text-lg font-semibold text-slate-900">Value Proposition</h2>
            <p className="text-slate-600 text-sm mt-1">
              What unique value do you bring to employers or clients?
            </p>
          </div>
          <div className="card-body">
            <div className="form-group">
              <label htmlFor="value_prop" className="form-label">
                Your Value Proposition
              </label>
              <textarea
                id="value_prop"
                value={formData.value_proposition || ''}
                onChange={(e) => handleChange('value_proposition', e.target.value)}
                className="input-field h-24"
                placeholder="Clearly state the benefits and outcomes you deliver"
              />
            </div>
          </div>
        </div>

        {/* Submit Button */}
        <div className="flex justify-end space-x-3">
          <button type="button" className="btn-secondary">
            Cancel
          </button>
          <button type="submit" className="btn-primary">
            Save Identity
          </button>
        </div>
      </form>
    </div>
  )
}
