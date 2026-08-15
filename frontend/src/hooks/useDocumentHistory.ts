import { useCallback, useEffect, useMemo, useState } from "react";
import { HISTORY_STORAGE_KEY } from "@/config";
import { listAllDocuments } from "@/services/documentService";
import { readJSON, writeJSON } from "@/utils/storage";
import type { DocumentCategory, DocumentHistoryEntry, DocumentStatus } from "@/types";

function generateId(): string {
  return `doc_${Date.now()}_${Math.random().toString(36).slice(2, 9)}`;
}

export interface UseDocumentHistoryResult {
  entries: DocumentHistoryEntry[];
  addPending: (tool: string, category: DocumentCategory, filename: string) => string;
  markSuccess: (id: string, message: string, serverPath?: string) => void;
  markError: (id: string, message: string) => void;
  removeEntry: (id: string) => void;
  clearHistory: () => void;
  refreshRemote: () => Promise<void>;
  remoteAvailable: boolean;
  isRefreshing: boolean;
}

/**
 * Historial de documentos generados. Combina dos fuentes:
 *
 *  1. Registro local (localStorage): cada llamada a una herramienta MCP
 *     realizada desde este navegador queda registrada de inmediato
 *     (pending -> success/error), independientemente de si el servidor
 *     expone o no un listado de archivos.
 *  2. Listado remoto (/files/<carpeta>/, servido por nginx con
 *     autoindex_format json): permite descubrir documentos generados por
 *     otras sesiones/clientes y enriquecer las entradas propias con tamano
 *     y fecha de modificacion reales. Si no esta disponible (dev sin proxy,
 *     backend sin desplegar la capa de archivos estaticos) la app degrada
 *     con elegancia y el historial local sigue siendo plenamente funcional.
 */
export function useDocumentHistory(): UseDocumentHistoryResult {
  const [entries, setEntries] = useState<DocumentHistoryEntry[]>(() =>
    readJSON(HISTORY_STORAGE_KEY, [] as DocumentHistoryEntry[]),
  );
  const [remoteAvailable, setRemoteAvailable] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    writeJSON(HISTORY_STORAGE_KEY, entries);
  }, [entries]);

  const addPending = useCallback(
    (tool: string, category: DocumentCategory, filename: string): string => {
      const id = generateId();
      const now = new Date().toISOString();
      const entry: DocumentHistoryEntry = {
        id,
        tool,
        category,
        filename,
        status: "pending" as DocumentStatus,
        message: "Generando documento...",
        createdAt: now,
        updatedAt: now,
      };
      setEntries((prev) => [entry, ...prev]);
      return id;
    },
    [],
  );

  const updateStatus = useCallback(
    (id: string, status: DocumentStatus, message: string, serverPath?: string) => {
      setEntries((prev) =>
        prev.map((e) =>
          e.id === id
            ? { ...e, status, message, serverPath, updatedAt: new Date().toISOString() }
            : e,
        ),
      );
    },
    [],
  );

  const markSuccess = useCallback(
    (id: string, message: string, serverPath?: string) =>
      updateStatus(id, "success", message, serverPath),
    [updateStatus],
  );

  const markError = useCallback(
    (id: string, message: string) => updateStatus(id, "error", message),
    [updateStatus],
  );

  const removeEntry = useCallback((id: string) => {
    setEntries((prev) => prev.filter((e) => e.id !== id));
  }, []);

  const clearHistory = useCallback(() => {
    setEntries([]);
  }, []);

  const refreshRemote = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const remoteFiles = await listAllDocuments();
      setRemoteAvailable(true);
      setEntries((prev) => {
        const byKey = new Map(prev.map((e) => [`${e.category}:${e.filename}`, e]));
        const next = [...prev];

        for (const remote of remoteFiles) {
          const key = `${remote.category}:${remote.filename}`;
          const existing = byKey.get(key);
          if (existing) {
            const idx = next.findIndex((e) => e.id === existing.id);
            if (idx >= 0) {
              next[idx] = {
                ...next[idx],
                sizeBytes: remote.sizeBytes,
                modifiedAt: remote.modifiedAt,
                status: next[idx].status === "pending" ? "success" : next[idx].status,
              };
            }
          } else {
            next.unshift({
              id: generateId(),
              tool: "",
              category: remote.category,
              filename: remote.filename,
              status: "success",
              message: "Documento detectado en el servidor.",
              createdAt: remote.modifiedAt,
              updatedAt: remote.modifiedAt,
              sizeBytes: remote.sizeBytes,
              modifiedAt: remote.modifiedAt,
              discovered: true,
            });
          }
        }
        return next;
      });
    } catch {
      setRemoteAvailable(false);
    } finally {
      setIsRefreshing(false);
    }
  }, []);

  useEffect(() => {
    void refreshRemote();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return useMemo(
    () => ({
      entries,
      addPending,
      markSuccess,
      markError,
      removeEntry,
      clearHistory,
      refreshRemote,
      remoteAvailable,
      isRefreshing,
    }),
    [
      entries,
      addPending,
      markSuccess,
      markError,
      removeEntry,
      clearHistory,
      refreshRemote,
      remoteAvailable,
      isRefreshing,
    ],
  );
}
