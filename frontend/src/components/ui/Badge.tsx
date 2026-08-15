import type { ReactNode } from "react";

type Tone = "purple" | "green" | "cyan" | "red" | "amber" | "slate";

const toneClasses: Record<Tone, string> = {
  purple: "bg-brand-purple-100 text-brand-purple-800 dark:bg-brand-purple-900/40 dark:text-brand-purple-300",
  green: "bg-brand-green-100 text-brand-green-800 dark:bg-brand-green-900/40 dark:text-brand-green-300",
  cyan: "bg-brand-cyan-100 text-brand-cyan-800 dark:bg-brand-cyan-900/40 dark:text-brand-cyan-300",
  red: "bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300",
  amber: "bg-amber-100 text-amber-800 dark:bg-amber-900/40 dark:text-amber-300",
  slate: "bg-slate-100 text-slate-700 dark:bg-slate-800 dark:text-slate-300",
};

export function Badge({ tone = "slate", children }: { tone?: Tone; children: ReactNode }) {
  return (
    <span
      className={[
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-xs font-medium",
        toneClasses[tone],
      ].join(" ")}
    >
      {children}
    </span>
  );
}
