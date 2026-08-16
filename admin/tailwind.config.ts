import type { Config } from 'tailwindcss'

export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        cyan: {
          50: '#ecf9fd',
          100: '#d4f1fa',
          200: '#b1e7f5',
          300: '#7ddbef',
          400: '#44cde5',
          500: '#22bfd4',
          600: '#16a3b8',
          700: '#168195',
          800: '#1a6a7b',
          900: '#1b5666',
          950: '#0d3946',
        },
        slate: {
          50: '#f8fafc',
          100: '#f1f5f9',
          200: '#e2e8f0',
          300: '#cbd5e1',
          400: '#94a3b8',
          500: '#64748b',
          600: '#475569',
          700: '#334155',
          800: '#1e293b',
          900: '#0f172a',
          950: '#020617',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} satisfies Config
