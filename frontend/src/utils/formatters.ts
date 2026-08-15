export function formatBytes(bytes: number): string {
  if (!Number.isFinite(bytes) || bytes < 0) return "-";
  if (bytes === 0) return "0 B";
  const units = ["B", "KB", "MB", "GB"];
  const exp = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  const value = bytes / 1024 ** exp;
  return `${value.toFixed(exp === 0 ? 0 : 1)} ${units[exp]}`;
}

export function formatDateTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  return new Intl.DateTimeFormat("es-MX", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(date);
}

export function formatRelativeTime(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return iso;
  const diffMs = date.getTime() - Date.now();
  const diffSec = Math.round(diffMs / 1000);
  const rtf = new Intl.RelativeTimeFormat("es-MX", { numeric: "auto" });

  const divisions: Array<[number, Intl.RelativeTimeFormatUnit]> = [
    [60, "seconds"],
    [60, "minutes"],
    [24, "hours"],
    [30, "days"],
    [12, "months"],
    [Number.POSITIVE_INFINITY, "years"],
  ];

  let duration = diffSec;
  for (const [amount, unit] of divisions) {
    if (Math.abs(duration) < amount) {
      return rtf.format(Math.round(duration), unit);
    }
    duration /= amount;
  }
  return rtf.format(Math.round(duration), "years");
}

// Rango Unicode de marcas diacriticas combinantes (U+0300 - U+036F), usado
// para eliminar acentos tras normalizar con NFD.
const COMBINING_DIACRITICS_RE = /[\u0300-\u036f]/g;

/** Genera un nombre de archivo seguro (sin espacios/acentos problematicos) con timestamp. */
export function buildFilename(prefix: string, displayName: string): string {
  const slug = displayName
    .normalize("NFD")
    .replace(COMBINING_DIACRITICS_RE, "")
    .replace(/[^a-zA-Z0-9]+/g, "_")
    .replace(/^_+|_+$/g, "")
    .toLowerCase();
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const base = slug || "documento";
  return `${prefix}_${base}_${stamp}.pdf`;
}

/** Formatea una fecha (yyyy-mm-dd) al formato largo en espanol usado en la carta. */
export function formatSpanishLongDate(isoDate: string): string {
  const date = isoDate ? new Date(`${isoDate}T00:00:00`) : new Date();
  if (Number.isNaN(date.getTime())) return isoDate;
  return new Intl.DateTimeFormat("es-MX", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(date);
}

export function extractServerPath(message: string): string | undefined {
  const match = message.match(/'([^']+\.pdf)'/i);
  return match?.[1];
}

export function isSuccessMessage(message: string): boolean {
  return /^\s*Éxito/i.test(message) || /^\s*Exito/i.test(message);
}
