import { FieldWrapper, Input } from "@/components/ui/Field";
import { RepeatableTextList } from "@/components/forms/RepeatableTextList";
import { formatSpanishLongDate } from "@/utils/formatters";
import type { CoverLetterData } from "@/types";
import type { ValidationIssue } from "@/utils/validators";

interface CoverLetterFormProps {
  value: CoverLetterData;
  onChange: (data: CoverLetterData) => void;
  errors: ValidationIssue[];
  disabled?: boolean;
}

export function CoverLetterForm({ value, onChange, errors, disabled }: CoverLetterFormProps) {
  const getError = (field: string) => errors.find((e) => e.field === field)?.message;

  const setEncabezado = (patch: Partial<CoverLetterData["encabezado"]>) =>
    onChange({ ...value, encabezado: { ...value.encabezado, ...patch } });

  // El campo "fecha" se guarda como texto largo en espanol (tal como lo
  // espera el template Jinja2), pero se edita con un <input type="date">
  // para mejor UX; se convierte automaticamente al formato esperado.
  const dateInputValue = (() => {
    const parsed = new Date(value.fecha);
    return Number.isNaN(parsed.getTime()) ? "" : value.fecha;
  })();

  return (
    <fieldset disabled={disabled} className="space-y-8">
      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Encabezado
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FieldWrapper label="Nombre completo" htmlFor="cover-nombre" required error={getError("encabezado.nombre")}>
            <Input
              id="cover-nombre"
              value={value.encabezado.nombre}
              error={!!getError("encabezado.nombre")}
              onChange={(e) => setEncabezado({ nombre: e.target.value })}
              placeholder="Juan García"
            />
          </FieldWrapper>
          <FieldWrapper label="Email" htmlFor="cover-email" required error={getError("encabezado.email")}>
            <Input
              id="cover-email"
              type="email"
              value={value.encabezado.email}
              error={!!getError("encabezado.email")}
              onChange={(e) => setEncabezado({ email: e.target.value })}
              placeholder="juan@example.com"
            />
          </FieldWrapper>
          <FieldWrapper label="Ubicación" htmlFor="cover-ubicacion">
            <Input
              id="cover-ubicacion"
              value={value.encabezado.ubicacion}
              onChange={(e) => setEncabezado({ ubicacion: e.target.value })}
              placeholder="Ciudad de México, México"
            />
          </FieldWrapper>
          <FieldWrapper label="Sitio web" htmlFor="cover-web">
            <Input
              id="cover-web"
              value={value.encabezado.sitio_web}
              onChange={(e) => setEncabezado({ sitio_web: e.target.value })}
              placeholder="tudominio.com"
            />
          </FieldWrapper>
          <FieldWrapper label="GitHub" htmlFor="cover-github">
            <Input
              id="cover-github"
              value={value.encabezado.github}
              onChange={(e) => setEncabezado({ github: e.target.value })}
              placeholder="github.com/usuario"
            />
          </FieldWrapper>
        </div>
      </section>

      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Destinatario
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FieldWrapper label="Empresa" htmlFor="cover-empresa" required error={getError("empresa")}>
            <Input
              id="cover-empresa"
              value={value.empresa}
              error={!!getError("empresa")}
              onChange={(e) => onChange({ ...value, empresa: e.target.value })}
              placeholder="Acme Inc."
            />
          </FieldWrapper>
          <FieldWrapper label="Fecha" htmlFor="cover-fecha" required error={getError("fecha")}>
            <Input
              id="cover-fecha"
              type="date"
              value={dateInputValue}
              onChange={(e) =>
                onChange({ ...value, fecha: formatSpanishLongDate(e.target.value) })
              }
            />
            {value.fecha && !dateInputValue && (
              <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                Fecha actual: <span className="font-medium">{value.fecha}</span>
              </p>
            )}
          </FieldWrapper>
        </div>
      </section>

      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Cuerpo de la carta
        </h3>
        <RepeatableTextList
          label="Párrafos"
          items={value.párrafos}
          onChange={(items) => onChange({ ...value, párrafos: items })}
          placeholder="Redacta un párrafo del cuerpo de la carta..."
          addLabel="Agregar párrafo"
          rows={4}
        />
        {getError("párrafos") && <p className="field-error">{getError("párrafos")}</p>}
      </section>
    </fieldset>
  );
}
