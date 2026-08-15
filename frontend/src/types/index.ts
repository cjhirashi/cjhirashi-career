// ---------------------------------------------------------------------------
// Tipos del dominio: estructuras de datos que aceptan las herramientas MCP
// crear_cv_pdf y crear_cover_letter_pdf.
//
// IMPORTANTE: estas interfaces reflejan EXACTAMENTE las claves consumidas por
// las plantillas Jinja2 del servidor (server/templates/cv_template.html y
// server/templates/cover_template.html), verificadas contra los datos de
// prueba reales en server/test_cv.py y server/test_cover.py. No coinciden con
// el esquema simplificado ("nombre/email/experiencia...") descrito de forma
// generica en la documentacion de alto nivel del agente frontend.
// ---------------------------------------------------------------------------

export interface CVEncabezado {
  nombre: string;
  subtitulo: string;
  email: string;
  telefono: string;
  ubicacion: string;
  sitio_web: string;
  linkedin: string;
  github: string;
}

export interface CVCompetencia {
  categoria: string;
  habilidades: string;
}

export interface CVExperiencia {
  empresa: string;
  puesto: string;
  periodo: string;
  puntos_clave: string[];
}

export interface CVEducacion {
  institucion: string;
  titulo: string;
  periodo: string;
  detalles: string;
}

export interface CVLogroDestacado {
  titulo: string;
  desafio: string;
  solucion: string;
  resultado: string;
}

export interface CVData {
  encabezado: CVEncabezado;
  resumen_ejecutivo: string[];
  competencias_clave: CVCompetencia[];
  experiencia: CVExperiencia[];
  educacion: CVEducacion[];
  logro_destacado: CVLogroDestacado;
  palabras_clave: string[];
}

export interface CoverLetterEncabezado {
  nombre: string;
  email: string;
  ubicacion: string;
  sitio_web: string;
  github: string;
}

export interface CoverLetterData {
  encabezado: CoverLetterEncabezado;
  fecha: string;
  empresa: string;
  // Nota: la clave real en el template Jinja2 es "párrafos" (con tilde).
  párrafos: string[];
}

// ---------------------------------------------------------------------------
// Registro de herramientas MCP conocidas por el frontend
// ---------------------------------------------------------------------------

export type KnownToolName = "crear_cv_pdf" | "crear_cover_letter_pdf";

export type DocumentCategory = "cv" | "cover_letter" | "generic";

export interface ToolDefinition {
  name: string;
  category: DocumentCategory;
  label: string;
  description: string;
  /** Subcarpeta dentro del volumen de salidas persistentes del servidor. */
  outputFolder: "cvs" | "cover_letters" | string;
  /** Nombre del argumento que contiene el JSON de datos (string serializado). */
  dataArgName: string;
  /** Nombre del argumento que contiene el nombre de archivo destino. */
  filenameArgName: string;
}

// ---------------------------------------------------------------------------
// Historial de documentos (persistido en localStorage por el cliente)
// ---------------------------------------------------------------------------

export type DocumentStatus = "pending" | "success" | "error";

export interface DocumentHistoryEntry {
  id: string;
  tool: string;
  category: DocumentCategory;
  filename: string;
  status: DocumentStatus;
  message: string;
  createdAt: string; // ISO 8601
  updatedAt: string; // ISO 8601
  /** Ruta absoluta reportada por el servidor (si status === 'success'). */
  serverPath?: string;
  /** true si esta entrada fue descubierta via listado remoto (/files) y no
   * generada en esta sesion/navegador. */
  discovered?: boolean;
  /** Metadatos enriquecidos desde el listado remoto (si disponible). */
  sizeBytes?: number;
  modifiedAt?: string;
}

// ---------------------------------------------------------------------------
// Listado remoto de archivos (nginx autoindex_format json)
// ---------------------------------------------------------------------------

export interface RemoteFileEntry {
  name: string;
  type: "file" | "directory";
  mtime: string;
  size: number;
}

export interface DocumentInfo {
  filename: string;
  category: DocumentCategory;
  sizeBytes: number;
  modifiedAt: string;
  downloadUrl: string;
}

// ---------------------------------------------------------------------------
// Cliente MCP (JSON-RPC 2.0 sobre SSE) - estado de conexion
// ---------------------------------------------------------------------------

export type ConnectionStatus =
  | "idle"
  | "connecting"
  | "connected"
  | "reconnecting"
  | "error"
  | "disconnected";

export interface MCPToolSummary {
  name: string;
  description?: string;
  inputSchema?: Record<string, unknown>;
}

export interface ToolCallResult {
  ok: boolean;
  text: string;
  raw?: unknown;
}

// ---------------------------------------------------------------------------
// JSON-RPC 2.0 (subconjunto usado por el transporte MCP SSE)
// ---------------------------------------------------------------------------

export interface JsonRpcRequest<TParams = unknown> {
  jsonrpc: "2.0";
  id?: number | string;
  method: string;
  params?: TParams;
}

export interface JsonRpcError {
  code: number;
  message: string;
  data?: unknown;
}

export interface JsonRpcResponse<TResult = unknown> {
  jsonrpc: "2.0";
  id: number | string;
  result?: TResult;
  error?: JsonRpcError;
}

// ---------------------------------------------------------------------------
// Toasts / notificaciones
// ---------------------------------------------------------------------------

export type ToastVariant = "success" | "error" | "info" | "warning";

export interface ToastMessage {
  id: string;
  variant: ToastVariant;
  title: string;
  description?: string;
  createdAt: number;
}

// ---------------------------------------------------------------------------
// Tema
// ---------------------------------------------------------------------------

export type ThemePreference = "light" | "dark" | "system";
