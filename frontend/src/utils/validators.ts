import type { CVData, CoverLetterData } from "@/types";

export interface ValidationIssue {
  field: string;
  message: string;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function pushIf(issues: ValidationIssue[], condition: boolean, field: string, message: string) {
  if (condition) issues.push({ field, message });
}

export function validateCVData(data: CVData): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  pushIf(issues, !data.encabezado.nombre.trim(), "encabezado.nombre", "El nombre es obligatorio.");
  pushIf(
    issues,
    !data.encabezado.email.trim() || !EMAIL_RE.test(data.encabezado.email.trim()),
    "encabezado.email",
    "Ingresa un correo electronico valido.",
  );
  pushIf(
    issues,
    data.resumen_ejecutivo.every((p) => !p.trim()),
    "resumen_ejecutivo",
    "Agrega al menos un parrafo de resumen ejecutivo.",
  );
  pushIf(
    issues,
    data.experiencia.length === 0,
    "experiencia",
    "Agrega al menos una experiencia laboral.",
  );
  data.experiencia.forEach((exp, i) => {
    pushIf(issues, !exp.empresa.trim(), `experiencia.${i}.empresa`, `Experiencia #${i + 1}: falta la empresa.`);
    pushIf(issues, !exp.puesto.trim(), `experiencia.${i}.puesto`, `Experiencia #${i + 1}: falta el puesto.`);
  });

  return issues;
}

export function validateCoverLetterData(data: CoverLetterData): ValidationIssue[] {
  const issues: ValidationIssue[] = [];

  pushIf(issues, !data.encabezado.nombre.trim(), "encabezado.nombre", "El nombre es obligatorio.");
  pushIf(
    issues,
    !data.encabezado.email.trim() || !EMAIL_RE.test(data.encabezado.email.trim()),
    "encabezado.email",
    "Ingresa un correo electronico valido.",
  );
  pushIf(issues, !data.empresa.trim(), "empresa", "El nombre de la empresa es obligatorio.");
  pushIf(issues, !data.fecha.trim(), "fecha", "La fecha es obligatoria.");
  pushIf(
    issues,
    data.párrafos.every((p) => !p.trim()),
    "párrafos",
    "Agrega al menos un parrafo en el cuerpo de la carta.",
  );

  return issues;
}

export function isValidJson(value: string): boolean {
  try {
    JSON.parse(value);
    return true;
  } catch {
    return false;
  }
}

export function validateFilename(value: string): ValidationIssue[] {
  const issues: ValidationIssue[] = [];
  pushIf(issues, !value.trim(), "nombre_archivo", "El nombre de archivo es obligatorio.");
  pushIf(
    issues,
    !!value && !/\.pdf$/i.test(value.trim()),
    "nombre_archivo",
    'El nombre de archivo debe terminar en ".pdf".',
  );
  pushIf(
    issues,
    /[\\/]/.test(value),
    "nombre_archivo",
    "El nombre de archivo no puede contener rutas (/ o \\).",
  );
  return issues;
}
