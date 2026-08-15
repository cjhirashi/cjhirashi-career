import { useToast } from "@/context/ToastContext";
import type { ToastVariant } from "@/types";

const VARIANT_CLASSES: Record<ToastVariant, string> = {
  success: "border-brand-green-500 bg-brand-green-50 text-brand-green-900 dark:bg-brand-green-950 dark:text-brand-green-200",
  error: "border-red-500 bg-red-50 text-red-900 dark:bg-red-950 dark:text-red-200",
  info: "border-brand-cyan-500 bg-brand-cyan-50 text-brand-cyan-900 dark:bg-brand-cyan-950 dark:text-brand-cyan-200",
  warning: "border-amber-500 bg-amber-50 text-amber-900 dark:bg-amber-950 dark:text-amber-200",
};

const VARIANT_ICON: Record<ToastVariant, string> = {
  success: "✓",
  error: "✕",
  info: "i",
  warning: "!",
};

export function NotificationCenter() {
  const { toasts, dismissToast } = useToast();

  return (
    <div
      className="pointer-events-none fixed bottom-4 right-4 z-[100] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-2 sm:w-full"
      role="region"
      aria-label="Notificaciones"
    >
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={[
            "pointer-events-auto flex items-start gap-3 rounded-lg border-l-4 bg-white p-3 shadow-lg animate-toast-in dark:bg-slate-900",
            VARIANT_CLASSES[toast.variant],
          ].join(" ")}
        >
          <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-current/10 text-xs font-bold">
            {VARIANT_ICON[toast.variant]}
          </span>
          <div className="flex-1">
            <p className="text-sm font-semibold">{toast.title}</p>
            {toast.description && <p className="mt-0.5 text-xs opacity-80">{toast.description}</p>}
          </div>
          <button
            type="button"
            onClick={() => dismissToast(toast.id)}
            aria-label="Cerrar notificación"
            className="focus-ring rounded p-0.5 text-current opacity-60 hover:opacity-100"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      ))}
    </div>
  );
}
