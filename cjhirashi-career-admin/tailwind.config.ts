import type { Config } from 'tailwindcss'

export default {
  // Dark mode is toggled via a `data-theme="dark"` attribute on <html>,
  // set by src/stores/themeStore.ts (and pre-applied by an inline script in
  // index.html to avoid a flash of incorrect theme). This uses Tailwind's
  // "selector" darkMode strategy (available since Tailwind 3.4.1) instead of
  // the default `.dark` class strategy.
  darkMode: ['selector', '[data-theme="dark"]'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // "Glass Steel" semantic tokens backed by CSS variables (see
        // src/index.css). Values automatically switch when `data-theme`
        // changes, so components using them (e.g. `bg-surface-card`,
        // `text-text`) don't need explicit `dark:` variants.
        bg: 'var(--bg-primary)',
        surface: 'var(--bg-secondary)',
        'surface-card': 'var(--bg-card)',
        glass: 'var(--bg-glass)',
        border: 'var(--border-glass)',
        'border-hover': 'var(--border-glass-hover)',
        text: 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        'text-muted': 'var(--text-muted)',
        primary: 'var(--primary-color)',
        'primary-hover': 'var(--primary-hover)',
        'primary-light': 'var(--primary-light)',
        'on-primary': 'var(--on-primary)',
        'primary-container': 'var(--primary-light)',
        secondary: 'var(--secondary-color)',
        'secondary-hover': 'var(--secondary-hover)',
        'secondary-light': 'var(--secondary-light)',
        'secondary-container': 'var(--secondary-light)',
        // cyan/slate intentionally left as Tailwind's built-in default
        // scales - they already match the Glass Steel reference palette
        // (cyan-600 #0891b2 == --primary-color, slate-900 #0f172a ==
        // --text-primary, etc.), so no override is needed here anymore.
      },
      fontFamily: {
        sans: ['system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Consolas', 'monospace'],
      },
      boxShadow: {
        glass: 'var(--shadow-glass)',
        glow: 'var(--shadow-glow)',
      },
    },
  },
  plugins: [],
} satisfies Config
