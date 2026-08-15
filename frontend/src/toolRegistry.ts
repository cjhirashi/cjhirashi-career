import type { ToolDefinition } from "@/types";

/**
 * Registro estatico de las herramientas MCP conocidas por este frontend.
 * Sirve como fuente de verdad para renderizar el formulario especializado
 * correcto (CVForm, CoverLetterForm) y para construir el payload de
 * argumentos esperado por server/server.py.
 *
 * Herramientas no listadas aqui pero reportadas por el servidor via
 * "tools/list" se muestran igualmente (ver DocumentForm.tsx) usando un
 * formulario JSON generico, para que agregar nuevas herramientas al
 * servidor no requiera cambios inmediatos en el frontend.
 */
export const KNOWN_TOOLS: ToolDefinition[] = [
  {
    name: "crear_cv_pdf",
    category: "cv",
    label: "Curriculum Vitae",
    description: "Genera un CV profesional en PDF a partir de una estructura JSON.",
    outputFolder: "cvs",
    dataArgName: "datos_cv_json",
    filenameArgName: "nombre_archivo",
  },
  {
    name: "crear_cover_letter_pdf",
    category: "cover_letter",
    label: "Carta de Presentación",
    description: "Genera una carta de presentación profesional en PDF a partir de una estructura JSON.",
    outputFolder: "cover_letters",
    dataArgName: "datos_cover_json",
    filenameArgName: "nombre_archivo",
  },
];

export function findToolDefinition(name: string): ToolDefinition | undefined {
  return KNOWN_TOOLS.find((t) => t.name === name);
}
