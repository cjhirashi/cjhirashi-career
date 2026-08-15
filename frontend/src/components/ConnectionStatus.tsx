import { useState } from "react";
import type { ConnectionStatus as Status } from "@/types";

interface ConnectionStatusProps {
  status: Status;
  error?: string;
  onReconnect: () => void;
}

const STATUS_CONFIG: Record<Status, { label: string; dot: string }> = {
  idle: { label: "Iniciando…", dot: "bg-slate-400" },
  connecting: { label: "Conectando…", dot: "bg-amber-400 animate-pulse" },
  connected: { label: "Conectado", dot: "bg-brand-green-500" },
  reconnecting: { label: "Reconectando…", dot: "bg-amber-400 animate-pulse" },
  error: { label: "Error de conexión", dot: "bg-red-500" },
  disconnected: { label: "Desconectado", dot: "bg-slate-400" },
};

export function ConnectionStatus({ status, error, onReconnect }: ConnectionStatusProps) {
  const [open, setOpen] = useState(false);
  const config = STATUS_CONFIG[status];
  const needsAction = status === "error" || status === "disconnected";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="focus-ring flex items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-600 transition-colors hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300 dark:hover:bg-slate-800"
      >
        <span className={`h-2 w-2 rounded-full ${config.dot}`} aria-hidden="true" />
        <span className="hidden sm:inline">{config.label}</span>
      </button>

      {open && (
        <div className="absolute right-0 z-40 mt-2 w-64 rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-lg dark:border-slate-700 dark:bg-slate-900">
          <p className="font-medium text-slate-800 dark:text-slate-100">{config.label}</p>
          {error && <p className="mt-1 text-xs text-red-600 dark:text-red-400">{error}</p>}
          <p className="mt-2 text-xs text-slate-500 dark:text-slate-400">
            El frontend se comunica con el servidor MCP vía SSE/JSON-RPC.
          </p>
          {needsAction && (
            <button
              type="button"
              onClick={() => {
                onReconnect();
                setOpen(false);
              }}
              className="focus-ring mt-3 w-full rounded-md bg-brand-purple-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-brand-purple-700"
            >
              Reconectar ahora
            </button>
          )}
        </div>
      )}
    </div>
  );
}
