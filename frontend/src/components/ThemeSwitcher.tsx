import type { ThemePreference } from "@/types";

interface ThemeSwitcherProps {
  preference: ThemePreference;
  onChange: (preference: ThemePreference) => void;
}

const OPTIONS: Array<{ value: ThemePreference; label: string; icon: JSX.Element }> = [
  {
    value: "light",
    label: "Claro",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="h-4 w-4">
        <circle cx="12" cy="12" r="4" strokeWidth={2} />
        <path
          strokeLinecap="round"
          strokeWidth={2}
          d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M4.93 19.07l1.41-1.41M17.66 6.34l1.41-1.41"
        />
      </svg>
    ),
  },
  {
    value: "system",
    label: "Sistema",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="h-4 w-4">
        <rect x="3" y="4" width="18" height="12" rx="2" strokeWidth={2} />
        <path strokeLinecap="round" strokeWidth={2} d="M8 20h8M12 16v4" />
      </svg>
    ),
  },
  {
    value: "dark",
    label: "Oscuro",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" className="h-4 w-4">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12.79A9 9 0 1111.21 3a7 7 0 009.79 9.79z" />
      </svg>
    ),
  },
];

export function ThemeSwitcher({ preference, onChange }: ThemeSwitcherProps) {
  return (
    <div className="inline-flex rounded-full border border-slate-200 bg-white p-0.5 dark:border-slate-700 dark:bg-slate-900">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          type="button"
          aria-label={`Tema ${opt.label}`}
          aria-pressed={preference === opt.value}
          onClick={() => onChange(opt.value)}
          className={[
            "focus-ring flex items-center gap-1 rounded-full px-2.5 py-1.5 text-xs font-medium transition-colors",
            preference === opt.value
              ? "bg-brand-purple-600 text-white"
              : "text-slate-500 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800",
          ].join(" ")}
        >
          {opt.icon}
          <span className="hidden md:inline">{opt.label}</span>
        </button>
      ))}
    </div>
  );
}
