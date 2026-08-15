import { FieldWrapper, Input, Textarea } from "@/components/ui/Field";
import { Button } from "@/components/ui/Button";
import { RepeatableTextList } from "@/components/forms/RepeatableTextList";
import type { CVData, CVExperiencia, CVEducacion, CVCompetencia } from "@/types";
import type { ValidationIssue } from "@/utils/validators";

interface CVFormProps {
  value: CVData;
  onChange: (data: CVData) => void;
  errors: ValidationIssue[];
  disabled?: boolean;
}

function useFieldError(errors: ValidationIssue[]) {
  return (field: string) => errors.find((e) => e.field === field)?.message;
}

export function CVForm({ value, onChange, errors, disabled }: CVFormProps) {
  const getError = useFieldError(errors);

  const setEncabezado = (patch: Partial<CVData["encabezado"]>) =>
    onChange({ ...value, encabezado: { ...value.encabezado, ...patch } });

  const setCompetencia = (index: number, patch: Partial<CVCompetencia>) => {
    const next = [...value.competencias_clave];
    next[index] = { ...next[index], ...patch };
    onChange({ ...value, competencias_clave: next });
  };

  const addCompetencia = () =>
    onChange({
      ...value,
      competencias_clave: [...value.competencias_clave, { categoria: "", habilidades: "" }],
    });

  const removeCompetencia = (index: number) =>
    onChange({
      ...value,
      competencias_clave: value.competencias_clave.filter((_, i) => i !== index),
    });

  const setExperiencia = (index: number, patch: Partial<CVExperiencia>) => {
    const next = [...value.experiencia];
    next[index] = { ...next[index], ...patch };
    onChange({ ...value, experiencia: next });
  };

  const addExperiencia = () =>
    onChange({
      ...value,
      experiencia: [
        ...value.experiencia,
        { empresa: "", puesto: "", periodo: "", puntos_clave: [""] },
      ],
    });

  const removeExperiencia = (index: number) =>
    onChange({ ...value, experiencia: value.experiencia.filter((_, i) => i !== index) });

  const setEducacion = (index: number, patch: Partial<CVEducacion>) => {
    const next = [...value.educacion];
    next[index] = { ...next[index], ...patch };
    onChange({ ...value, educacion: next });
  };

  const addEducacion = () =>
    onChange({
      ...value,
      educacion: [...value.educacion, { institucion: "", titulo: "", periodo: "", detalles: "" }],
    });

  const removeEducacion = (index: number) =>
    onChange({ ...value, educacion: value.educacion.filter((_, i) => i !== index) });

  return (
    <fieldset disabled={disabled} className="space-y-8">
      {/* Encabezado */}
      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Encabezado
        </h3>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <FieldWrapper label="Nombre completo" htmlFor="cv-nombre" required error={getError("encabezado.nombre")}>
            <Input
              id="cv-nombre"
              value={value.encabezado.nombre}
              error={!!getError("encabezado.nombre")}
              onChange={(e) => setEncabezado({ nombre: e.target.value })}
              placeholder="Juan García"
            />
          </FieldWrapper>
          <FieldWrapper label="Subtítulo / puesto objetivo" htmlFor="cv-subtitulo">
            <Input
              id="cv-subtitulo"
              value={value.encabezado.subtitulo}
              onChange={(e) => setEncabezado({ subtitulo: e.target.value })}
              placeholder="Senior Software Engineer"
            />
          </FieldWrapper>
          <FieldWrapper label="Email" htmlFor="cv-email" required error={getError("encabezado.email")}>
            <Input
              id="cv-email"
              type="email"
              value={value.encabezado.email}
              error={!!getError("encabezado.email")}
              onChange={(e) => setEncabezado({ email: e.target.value })}
              placeholder="juan@example.com"
            />
          </FieldWrapper>
          <FieldWrapper label="Teléfono" htmlFor="cv-telefono">
            <Input
              id="cv-telefono"
              value={value.encabezado.telefono}
              onChange={(e) => setEncabezado({ telefono: e.target.value })}
              placeholder="+52 55 1234 5678"
            />
          </FieldWrapper>
          <FieldWrapper label="Ubicación" htmlFor="cv-ubicacion">
            <Input
              id="cv-ubicacion"
              value={value.encabezado.ubicacion}
              onChange={(e) => setEncabezado({ ubicacion: e.target.value })}
              placeholder="Ciudad de México, México"
            />
          </FieldWrapper>
          <FieldWrapper label="Sitio web" htmlFor="cv-web">
            <Input
              id="cv-web"
              value={value.encabezado.sitio_web}
              onChange={(e) => setEncabezado({ sitio_web: e.target.value })}
              placeholder="tudominio.com"
            />
          </FieldWrapper>
          <FieldWrapper label="LinkedIn" htmlFor="cv-linkedin">
            <Input
              id="cv-linkedin"
              value={value.encabezado.linkedin}
              onChange={(e) => setEncabezado({ linkedin: e.target.value })}
              placeholder="linkedin.com/in/usuario"
            />
          </FieldWrapper>
          <FieldWrapper label="GitHub" htmlFor="cv-github">
            <Input
              id="cv-github"
              value={value.encabezado.github}
              onChange={(e) => setEncabezado({ github: e.target.value })}
              placeholder="github.com/usuario"
            />
          </FieldWrapper>
        </div>
      </section>

      {/* Resumen ejecutivo */}
      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Resumen Ejecutivo
        </h3>
        <RepeatableTextList
          label="Párrafos del resumen"
          items={value.resumen_ejecutivo}
          onChange={(items) => onChange({ ...value, resumen_ejecutivo: items })}
          placeholder="Describe brevemente tu perfil profesional..."
          addLabel="Agregar párrafo"
          minItems={0}
        />
        {getError("resumen_ejecutivo") && <p className="field-error">{getError("resumen_ejecutivo")}</p>}
      </section>

      {/* Competencias clave */}
      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Competencias Clave
        </h3>
        <div className="space-y-3">
          {value.competencias_clave.map((comp, i) => (
            <div key={i} className="card grid grid-cols-1 gap-3 p-3 sm:grid-cols-[1fr_2fr_auto]">
              <Input
                aria-label="Categoría"
                value={comp.categoria}
                onChange={(e) => setCompetencia(i, { categoria: e.target.value })}
                placeholder="Categoría (ej. Sistemas & IA)"
              />
              <Input
                aria-label="Habilidades"
                value={comp.habilidades}
                onChange={(e) => setCompetencia(i, { habilidades: e.target.value })}
                placeholder="Habilidades separadas por coma"
              />
              <Button type="button" variant="ghost" size="sm" onClick={() => removeCompetencia(i)}>
                Quitar
              </Button>
            </div>
          ))}
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={addCompetencia}>
          + Agregar competencia
        </Button>
      </section>

      {/* Experiencia */}
      <section className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
            Experiencia {getError("experiencia") && <span className="text-red-500">*</span>}
          </h3>
        </div>
        {getError("experiencia") && <p className="field-error">{getError("experiencia")}</p>}
        <div className="space-y-4">
          {value.experiencia.map((exp, i) => (
            <div key={i} className="card space-y-3 p-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <Input
                  value={exp.empresa}
                  error={!!getError(`experiencia.${i}.empresa`)}
                  onChange={(e) => setExperiencia(i, { empresa: e.target.value })}
                  placeholder="Empresa"
                />
                <Input
                  value={exp.puesto}
                  error={!!getError(`experiencia.${i}.puesto`)}
                  onChange={(e) => setExperiencia(i, { puesto: e.target.value })}
                  placeholder="Puesto"
                />
                <Input
                  value={exp.periodo}
                  onChange={(e) => setExperiencia(i, { periodo: e.target.value })}
                  placeholder="Periodo (ej. 2020 - Actualidad)"
                />
              </div>
              <RepeatableTextList
                label="Puntos clave"
                items={exp.puntos_clave}
                onChange={(items) => setExperiencia(i, { puntos_clave: items })}
                placeholder="Logro o responsabilidad destacada"
                addLabel="Agregar punto"
                rows={1}
              />
              <div className="flex justify-end">
                <Button type="button" variant="ghost" size="sm" onClick={() => removeExperiencia(i)}>
                  Quitar experiencia
                </Button>
              </div>
            </div>
          ))}
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={addExperiencia}>
          + Agregar experiencia
        </Button>
      </section>

      {/* Educación */}
      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Educación & Certificaciones
        </h3>
        <div className="space-y-3">
          {value.educacion.map((edu, i) => (
            <div key={i} className="card space-y-3 p-4">
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
                <Input
                  value={edu.institucion}
                  onChange={(e) => setEducacion(i, { institucion: e.target.value })}
                  placeholder="Institución"
                />
                <Input
                  value={edu.titulo}
                  onChange={(e) => setEducacion(i, { titulo: e.target.value })}
                  placeholder="Título / Certificación"
                />
                <Input
                  value={edu.periodo}
                  onChange={(e) => setEducacion(i, { periodo: e.target.value })}
                  placeholder="Periodo"
                />
              </div>
              <Textarea
                rows={2}
                value={edu.detalles}
                onChange={(e) => setEducacion(i, { detalles: e.target.value })}
                placeholder="Detalles adicionales (opcional)"
              />
              <div className="flex justify-end">
                <Button type="button" variant="ghost" size="sm" onClick={() => removeEducacion(i)}>
                  Quitar
                </Button>
              </div>
            </div>
          ))}
        </div>
        <Button type="button" variant="ghost" size="sm" onClick={addEducacion}>
          + Agregar educación
        </Button>
      </section>

      {/* Logro destacado */}
      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Logro Destacado
        </h3>
        <div className="card grid grid-cols-1 gap-3 p-4">
          <Input
            value={value.logro_destacado.titulo}
            onChange={(e) =>
              onChange({ ...value, logro_destacado: { ...value.logro_destacado, titulo: e.target.value } })
            }
            placeholder="Título del logro"
          />
          <Textarea
            rows={2}
            value={value.logro_destacado.desafio}
            onChange={(e) =>
              onChange({ ...value, logro_destacado: { ...value.logro_destacado, desafio: e.target.value } })
            }
            placeholder="Desafío"
          />
          <Textarea
            rows={2}
            value={value.logro_destacado.solucion}
            onChange={(e) =>
              onChange({ ...value, logro_destacado: { ...value.logro_destacado, solucion: e.target.value } })
            }
            placeholder="Solución"
          />
          <Textarea
            rows={2}
            value={value.logro_destacado.resultado}
            onChange={(e) =>
              onChange({ ...value, logro_destacado: { ...value.logro_destacado, resultado: e.target.value } })
            }
            placeholder="Resultado"
          />
        </div>
      </section>

      {/* Palabras clave */}
      <section className="space-y-4">
        <h3 className="text-sm font-semibold uppercase tracking-wide text-brand-purple-600 dark:text-brand-purple-400">
          Palabras Clave
        </h3>
        <FieldWrapper label="Separadas por coma" htmlFor="cv-keywords">
          <Input
            id="cv-keywords"
            value={value.palabras_clave.join(", ")}
            onChange={(e) =>
              onChange({
                ...value,
                palabras_clave: e.target.value
                  .split(",")
                  .map((k) => k.trim())
                  .filter(Boolean),
              })
            }
            placeholder="Python, Agentic AI, Docker"
          />
        </FieldWrapper>
      </section>
    </fieldset>
  );
}
