import { useMemo, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/context/ToastContext";
import { getDownloadUrl } from "@/services/documentService";
import { formatBytes, formatRelativeTime } from "@/utils/formatters";
import type { DocumentCategory, DocumentHistoryEntry, DocumentStatus } from "@/types";

interface DocumentHistoryProps {
  entries: DocumentHistoryEntry[];
  onRemove: (id: string) => void;
  onPreview: (entry: DocumentHistoryEntry) => void;
  onRefresh: () => void;
  remoteAvailable: boolean;
  isRefreshing: boolean;
}

const CATEGORY_LABEL: Record<DocumentCategory, string> = {
  cv: "CV",
  cover_letter: "Carta",
  generic: "Otro",
};

const CATEGORY_TONE: Record<DocumentCategory, "purple" | "cyan" | "slate"> = {
  cv: "purple",
  cover_letter: "cyan",
  generic: "slate",
};

const STATUS_CONFIG: Record<DocumentStatus, { label: string; tone: "green" | "red" | "amber" }> = {
  success: { label: "Completado", tone: "green" },
  error: { label: "Error", tone: "red" },
  pending: { label: "Generando…", tone: "amber" },
};

type FilterValue = "all" | DocumentCategory;

export function DocumentHistory({
  entries,
  onRemove,
  onPreview,
  onRefresh,
  remoteAvailable,
  isRefreshing,
}: DocumentHistoryProps) {
  const [filter, setFilter] = useState<FilterValue>("all");
  const { showToast } = useToast();

  const filtered = useMemo(
    () => (filter === "all" ? entries : entries.filter((e) => e.category === filter)),
    [entries, filter],
  );

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      showToast("info", "Copiado al portapapeles");
    } catch {
      showToast("error", "No se pudo copiar", "El navegador bloqueó el acceso al portapapeles.");
    }
  };

  return (
    <div className="card p-4 sm:p-6">
      <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
        <h2 className="text-base font-semibold text-slate-900 dark:text-slate-100">
          Historial de Documentos
        </h2>
        <div className="flex items-center gap-2">
          {!remoteAvailable && (
            <span className="text-xs text-amber-600 dark:text-amber-400" title="El listado remoto de archivos no está disponible; se muestra solo el historial local.">
              Listado remoto no disponible
            </span>
          )}
          <Button variant="ghost" size="sm" onClick={onRefresh} isLoading={isRefreshing}>
            Actualizar
          </Button>
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2">
        {(["all", "cv", "cover_letter", "generic"] as FilterValue[]).map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={[
              "focus-ring rounded-full px-3 py-1 text-xs font-medium transition-colors",
              filter === f
                ? "bg-brand-cyan-600 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700",
            ].join(" ")}
          >
            {f === "all" ? "Todos" : CATEGORY_LABEL[f]}
          </button>
        ))}
      </div>

      {filtered.length === 0 ? (
        <p className="py-10 text-center text-sm text-slate-400">
          Aún no hay documentos {filter !== "all" ? `de tipo "${CATEGORY_LABEL[filter as DocumentCategory]}"` : ""}.
        </p>
      ) : (
        <ul className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((entry) => {
            const status = STATUS_CONFIG[entry.status];
            const downloadUrl =
              entry.status === "success" && entry.category !== "generic"
                ? getDownloadUrl(entry.category, entry.filename)
                : undefined;

            return (
              <li key={entry.id} className="flex flex-col justify-between rounded-lg border border-slate-200 p-3 dark:border-slate-800">
                <div>
                  <div className="mb-1 flex items-center gap-2">
                    <Badge tone={CATEGORY_TONE[entry.category]}>{CATEGORY_LABEL[entry.category]}</Badge>
                    <Badge tone={status.tone}>{status.label}</Badge>
                    {entry.discovered && <Badge tone="slate">Detectado</Badge>}
                  </div>
                  <p className="truncate text-sm font-medium text-slate-900 dark:text-slate-100" title={entry.filename}>
                    {entry.filename}
                  </p>
                  <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                    {formatRelativeTime(entry.updatedAt)}
                    {typeof entry.sizeBytes === "number" && ` · ${formatBytes(entry.sizeBytes)}`}
                  </p>
                  {entry.status === "error" && (
                    <p className="mt-1 line-clamp-2 text-xs text-red-600 dark:text-red-400">{entry.message}</p>
                  )}
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  {downloadUrl && (
                    <>
                      <Button size="sm" variant="secondary" onClick={() => onPreview(entry)}>
                        Vista previa
                      </Button>
                      <a href={downloadUrl} download={entry.filename}>
                        <Button size="sm" variant="success" type="button">
                          Descargar
                        </Button>
                      </a>
                    </>
                  )}
                  <Button size="sm" variant="ghost" onClick={() => copyToClipboard(entry.serverPath ?? entry.filename)}>
                    Copiar ruta
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => onRemove(entry.id)}>
                    Quitar
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
