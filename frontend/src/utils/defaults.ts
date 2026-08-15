import type { CVData, CoverLetterData } from "@/types";

export function emptyCVData(): CVData {
  return {
    encabezado: {
      nombre: "",
      subtitulo: "",
      email: "",
      telefono: "",
      ubicacion: "",
      sitio_web: "",
      linkedin: "",
      github: "",
    },
    resumen_ejecutivo: [""],
    competencias_clave: [{ categoria: "", habilidades: "" }],
    experiencia: [{ empresa: "", puesto: "", periodo: "", puntos_clave: [""] }],
    educacion: [{ institucion: "", titulo: "", periodo: "", detalles: "" }],
    logro_destacado: { titulo: "", desafio: "", solucion: "", resultado: "" },
    palabras_clave: [],
  };
}

export function emptyCoverLetterData(): CoverLetterData {
  return {
    encabezado: {
      nombre: "",
      email: "",
      ubicacion: "",
      sitio_web: "",
      github: "",
    },
    fecha: "",
    empresa: "",
    párrafos: [""],
  };
}
