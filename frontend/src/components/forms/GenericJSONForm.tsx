import { FieldWrapper, Textarea } from "@/components/ui/Field";
import { isValidJson } from "@/utils/validators";
import type { MCPToolSummary } from "@/types";

interface GenericJSONFormProps {
  tool: MCPToolSummary;
  value: string;
  onChange: (value: string) => void;
  disabled?: boolean;
}

/**
 * Formulario de respaldo para herramientas MCP descubiertas dinamicamente
 * (via tools/list) que aun no tienen un formulario especializado en este
 * frontend. Permite editar directamente el objeto de argumentos como JSON,
 * garantizando que agregar nuevas herramientas al servidor no bloquea su
 * uso desde la UI mientras se desarrolla un formulario dedicado.
 */
export function GenericJSONForm({ tool, value, onChange, disabled }: GenericJSONFormProps) {
  const valid = value.trim().length === 0 || isValidJson(value);

  return (
    <fieldset disabled={disabled} className="space-y-4">
      <div className="card p-4">
        <p className="text-sm text-slate-600 dark:text-slate-400">
          {tool.description || "Herramienta MCP sin formulario dedicado todavía."}
        </p>
        {tool.inputSchema && (
          <pre className="mt-2 max-h-40 overflow-auto rounded-lg bg-slate-100 p-2 text-xs text-slate-600 dark:bg-slate-800 dark:text-slate-400">
            {JSON.stringify(tool.inputSchema, null, 2)}
          </pre>
        )}
      </div>
      <FieldWrapper
        label="Argumentos (JSON)"
        htmlFor="generic-json"
        required
        hint="Objeto JSON con los argumentos que espera esta herramienta."
        error={!valid ? "El JSON no es valido." : undefined}
      >
        <Textarea
          id="generic-json"
          rows={10}
          value={value}
          error={!valid}
          onChange={(e) => onChange(e.target.value)}
          placeholder='{"nombre_archivo": "documento.pdf", "...": "..."}'
          className="font-mono"
        />
      </FieldWrapper>
    </fieldset>
  );
}
