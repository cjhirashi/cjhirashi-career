import { getFilesBaseUrl } from "@/config";
import type { DocumentCategory, DocumentInfo, RemoteFileEntry } from "@/types";

// Carpetas reales dentro del volumen persistente del servidor MCP
// (server/tools/cv_generator.py y cover_generator.py), servidas de forma
// estatica y de solo lectura por nginx bajo /files/<carpeta>/ (ver
// frontend/nginx.conf). Este mapeo es la unica fuente de verdad frontend
// <-> estructura de carpetas del servidor.
const CATEGORY_FOLDERS: Record<Exclude<DocumentCategory, "generic">, string> = {
  cv: "cvs",
  cover_letter: "cover_letters",
};

export class DocumentServiceError extends Error {
  constructor(message: string, readonly cause?: unknown) {
    super(message);
    this.name = "DocumentServiceError";
  }
}

function folderFor(category: DocumentCategory): string {
  if (category === "generic") return "misc";
  return CATEGORY_FOLDERS[category];
}

export function getDownloadUrl(category: DocumentCategory, filename: string): string {
  const base = getFilesBaseUrl().replace(/\/$/, "");
  return `${base}/${folderFor(category)}/${encodeURIComponent(filename)}`;
}

/**
 * Lista los archivos disponibles para una categoria consultando el listado
 * JSON expuesto por nginx (`autoindex_format json;`). Si el endpoint no
 * existe (p. ej. en desarrollo sin el proxy configurado, o si el backend
 * aun no ha sido desplegado con esta capacidad) se lanza
 * DocumentServiceError y el llamador debe degradar con elegancia (el
 * historial local sigue funcionando de forma independiente).
 */
export async function listDocuments(category: DocumentCategory): Promise<DocumentInfo[]> {
  const base = getFilesBaseUrl().replace(/\/$/, "");
  const url = `${base}/${folderFor(category)}/`;

  let res: Response;
  try {
    res = await fetch(url, { headers: { Accept: "application/json" } });
  } catch (err) {
    throw new DocumentServiceError(
      "No se pudo contactar el listado de archivos del servidor",
      err,
    );
  }

  if (!res.ok) {
    throw new DocumentServiceError(
      `El listado de archivos respondio con HTTP ${res.status}`,
    );
  }

  const contentType = res.headers.get("content-type") ?? "";
  if (!contentType.includes("application/json")) {
    throw new DocumentServiceError(
      "El endpoint de archivos no devolvio JSON (revisar autoindex_format en nginx)",
    );
  }

  const entries = (await res.json()) as RemoteFileEntry[];
  return entries
    .filter((e) => e.type === "file" && e.name.toLowerCase().endsWith(".pdf"))
    .map((e) => ({
      filename: e.name,
      category,
      sizeBytes: e.size,
      modifiedAt: e.mtime,
      downloadUrl: getDownloadUrl(category, e.name),
    }))
    .sort((a, b) => (a.modifiedAt < b.modifiedAt ? 1 : -1));
}

export async function listAllDocuments(): Promise<DocumentInfo[]> {
  const results = await Promise.allSettled([
    listDocuments("cv"),
    listDocuments("cover_letter"),
  ]);
  return results.flatMap((r) => (r.status === "fulfilled" ? r.value : []));
}
