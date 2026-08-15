import { useEffect, useMemo, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Field";
import { CVForm } from "@/components/forms/CVForm";
import { CoverLetterForm } from "@/components/forms/CoverLetterForm";
import { GenericJSONForm } from "@/components/forms/GenericJSONForm";
import { useToast } from "@/context/ToastContext";
import { useDraft } from "@/hooks/useDraft";
import type { UseDocumentHistoryResult } from "@/hooks/useDocumentHistory";
import { KNOWN_TOOLS } from "@/toolRegistry";
import { emptyCVData, emptyCoverLetterData } from "@/utils/defaults";
import { buildFilename, extractServerPath, isSuccessMessage } from "@/utils/formatters";
import { readJSON, writeJSON } from "@/utils/storage";
import { validateCVData, validateCoverLetterData, isValidJson, type ValidationIssue } from "@/utils/validators";
import type { ConnectionStatus, MCPToolSummary, ToolCallResult, ToolDefinition } from "@/types";

interface DocumentFormProps {
  connectionStatus: ConnectionStatus;
  discoveredTools: MCPToolSummary[];
  callTool: (name: string, args: Record<string, unknown>) => Promise<ToolCallResult>;
  history: UseDocumentHistoryResult;
}

const GENERIC_DRAFTS_KEY = "mcp-frontend:generic-drafts:v1";

export function DocumentForm({ connectionStatus, discoveredTools, callTool, history }: DocumentFormProps) {
  const { showToast } = useToast();

  const tools: ToolDefinition[] = useMemo(() => {
    const extras: ToolDefinition[] = discoveredTools
      .filter((t) => !KNOWN_TOOLS.some((k) => k.name === t.name))
      .map((t) => ({
        name: t.name,
        category: "generic",
        label: t.name,
        description: t.description ?? "Herramienta MCP adicional.",
        outputFolder: "misc",
        dataArgName: "",
        filenameArgName: "",
      }));
    return [...KNOWN_TOOLS, ...extras];
  }, [discoveredTools]);

  const [selectedName, setSelectedName] = useState<string>(KNOWN_TOOLS[0].name);
  const selectedTool = tools.find((t) => t.name === selectedName) ?? tools[0];

  const cvDraft = useDraft("cv-data", emptyCVData());
  const cvFilenameDraft = useDraft("cv-filename", "");
  const coverDraft = useDraft("cover-data", emptyCoverLetterData());
  const coverFilenameDraft = useDraft("cover-filename", "");

  const [genericDrafts, setGenericDrafts] = useState<Record<string, { args: string; filename: string }>>(
    () => readJSON(GENERIC_DRAFTS_KEY, {}),
  );
  useEffect(() => {
    writeJSON(GENERIC_DRAFTS_KEY, genericDrafts);
  }, [genericDrafts]);

  const [errors, setErrors] = useState<ValidationIssue[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const formRef = useRef<HTMLDivElement>(null);

  const disabled = connectionStatus !== "connected" || isSubmitting;

  const genericValue = selectedTool?.category === "generic"
    ? genericDrafts[selectedTool.name] ?? { args: "{}", filename: "documento.pdf" }
    : { args: "{}", filename: "documento.pdf" };

  const setGenericValue = (patch: Partial<{ args: string; filename: string }>) => {
    if (!selectedTool) return;
    setGenericDrafts((prev) => ({
      ...prev,
      [selectedTool.name]: { ...genericValue, ...patch },
    }));
  };

  async function handleSubmit() {
    if (!selectedTool || isSubmitting) return;
    setErrors([]);

    if (connectionStatus !== "connected") {
      showToast("warning", "Sin conexión", "Conecta con el servidor MCP antes de generar un documento.");
      return;
    }

    if (selectedTool.category === "cv") {
      const issues = validateCVData(cvDraft.value);
      if (issues.length > 0) {
        setErrors(issues);
        showToast("error", "Formulario incompleto", issues[0].message);
        return;
      }
      const filename = cvFilenameDraft.value.trim() || buildFilename("CV", cvDraft.value.encabezado.nombre);
      await runToolCall("crear_cv_pdf", "cv", filename, {
        datos_cv_json: JSON.stringify(cvDraft.value),
        nombre_archivo: filename,
      }, () => {
        cvDraft.clearDraft();
        cvFilenameDraft.clearDraft();
      });
      return;
    }

    if (selectedTool.category === "cover_letter") {
      const issues = validateCoverLetterData(coverDraft.value);
      if (issues.length > 0) {
        setErrors(issues);
        showToast("error", "Formulario incompleto", issues[0].message);
        return;
      }
      const filename =
        coverFilenameDraft.value.trim() || buildFilename("CoverLetter", coverDraft.value.encabezado.nombre);
      await runToolCall("crear_cover_letter_pdf", "cover_letter", filename, {
        datos_cover_json: JSON.stringify(coverDraft.value),
        nombre_archivo: filename,
      }, () => {
        coverDraft.clearDraft();
        coverFilenameDraft.clearDraft();
      });
      return;
    }

    // Herramienta generica descubierta dinamicamente
    if (!isValidJson(genericValue.args)) {
      showToast("error", "JSON inválido", "Revisa los argumentos antes de enviar.");
      return;
    }
    const parsedArgs = JSON.parse(genericValue.args) as Record<string, unknown>;
    const filename = genericValue.filename.trim() || "documento.pdf";
    await runToolCall(selectedTool.name, "generic", filename, parsedArgs, () => {
      setGenericValue({ args: "{}", filename: "documento.pdf" });
    });
  }

  async function runToolCall(
    toolName: string,
    category: "cv" | "cover_letter" | "generic",
    filename: string,
    args: Record<string, unknown>,
    onSuccessCleanup: () => void,
  ) {
    setIsSubmitting(true);
    const entryId = history.addPending(toolName, category, filename);
    try {
      const result = await callTool(toolName, args);
      const success = result.ok && isSuccessMessage(result.text);
      if (success) {
        const serverPath = extractServerPath(result.text);
        history.markSuccess(entryId, result.text, serverPath);
        showToast("success", "Documento generado", filename);
        onSuccessCleanup();
        void history.refreshRemote();
      } else {
        history.markError(entryId, result.text || "El servidor reportó un error desconocido.");
        showToast("error", "Error al generar el documento", result.text);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : "Error desconocido";
      history.markError(entryId, message);
      showToast("error", "Error de comunicación con el servidor MCP", message);
    } finally {
      setIsSubmitting(false);
    }
  }

  // Atajo de teclado: Ctrl/Cmd + Enter envia el formulario activo
  useEffect(() => {
    const node = formRef.current;
    if (!node) return;
    const handler = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
        e.preventDefault();
        void handleSubmit();
      }
    };
    node.addEventListener("keydown", handler);
    return () => node.removeEventListener("keydown", handler);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTool, cvDraft.value, coverDraft.value, genericValue.args, connectionStatus, isSubmitting]);

  return (
    <div ref={formRef} className="card p-4 sm:p-6">
      {/* Tabs de herramientas */}
      <div className="mb-6 flex flex-wrap gap-2 border-b border-slate-200 pb-4 dark:border-slate-800">
        {tools.map((tool) => (
          <button
            key={tool.name}
            type="button"
            onClick={() => {
              setSelectedName(tool.name);
              setErrors([]);
            }}
            className={[
              "focus-ring rounded-lg px-3 py-2 text-sm font-medium transition-colors",
              selectedName === tool.name
                ? "bg-brand-purple-600 text-white"
                : "bg-slate-100 text-slate-700 hover:bg-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:hover:bg-slate-700",
            ].join(" ")}
          >
            {tool.label}
          </button>
        ))}
      </div>

      {selectedTool?.description && (
        <p className="mb-4 text-sm text-slate-500 dark:text-slate-400">{selectedTool.description}</p>
      )}

      {selectedTool?.category === "cv" && (
        <CVForm value={cvDraft.value} onChange={cvDraft.setValue} errors={errors} disabled={disabled} />
      )}
      {selectedTool?.category === "cover_letter" && (
        <CoverLetterForm value={coverDraft.value} onChange={coverDraft.setValue} errors={errors} disabled={disabled} />
      )}
      {selectedTool?.category === "generic" && (
        <GenericJSONForm
          tool={discoveredTools.find((t) => t.name === selectedTool.name) ?? { name: selectedTool.name }}
          value={genericValue.args}
          onChange={(v) => setGenericValue({ args: v })}
          disabled={disabled}
        />
      )}

      {/* Nombre de archivo + accion */}
      <div className="mt-6 flex flex-col gap-3 border-t border-slate-200 pt-4 dark:border-slate-800 sm:flex-row sm:items-end sm:justify-between">
        <div className="w-full sm:max-w-xs">
          <label htmlFor="filename" className="label">
            Nombre de archivo
          </label>
          <Input
            id="filename"
            className="mt-1"
            disabled={disabled}
            placeholder={
              selectedTool?.category === "cv"
                ? buildFilename("CV", cvDraft.value.encabezado.nombre || "documento")
                : selectedTool?.category === "cover_letter"
                  ? buildFilename("CoverLetter", coverDraft.value.encabezado.nombre || "documento")
                  : "documento.pdf"
            }
            value={
              selectedTool?.category === "cv"
                ? cvFilenameDraft.value
                : selectedTool?.category === "cover_letter"
                  ? coverFilenameDraft.value
                  : genericValue.filename
            }
            onChange={(e) => {
              if (selectedTool?.category === "cv") cvFilenameDraft.setValue(e.target.value);
              else if (selectedTool?.category === "cover_letter") coverFilenameDraft.setValue(e.target.value);
              else setGenericValue({ filename: e.target.value });
            }}
          />
          <p className="mt-1 text-xs text-slate-400">Si se deja vacío, se genera automáticamente.</p>
        </div>

        <div className="flex items-center gap-3">
          <span className="hidden text-xs text-slate-400 sm:inline">Ctrl + Enter para enviar</span>
          <Button type="button" onClick={() => void handleSubmit()} isLoading={isSubmitting} disabled={disabled}>
            Generar documento
          </Button>
        </div>
      </div>
    </div>
  );
}
