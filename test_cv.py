import os
from tools.cv_generator import generar_cv

# Datos de prueba con la estructura exacta que enviará la IA por MCP
datos_de_prueba = {
    "encabezado": {
        "nombre": "Carlos Jiménez Hirashi",
        "subtitulo": "AI Solutions Architect | Intelligent Automation",
        "email": "carlos@cjhirashi.com",
        "telefono": "+52 (55) 1371-0160",
        "ubicacion": "Ciudad de México, México",
        "sitio_web": "cjhirashi.com",
        "linkedin": "linkedin.com/in/cjhirashi",
        "github": "github.com/cjhirashi"
    },
    "resumen_ejecutivo": [
        "Arquitecto especializado en la automatización e integración de sistemas críticos con más de 20 años de experiencia en diseño de ingeniería y control.",
        "Actualmente enfocado en el desarrollo de arquitecturas de IA agéntica, Context Engineering y modelos de aprendizaje complejos para la toma de decisiones autónoma."
    ],
    "competencias_clave": [
        {
            "categoria": "Sistemas & IA",
            "habilidades": "Python, Context Engineering, Agentic AI, Multi-Agent Systems, SQL, Docker"
        },
        {
            "categoria": "Automatización",
            "habilidades": "BMS, BACnet, Control Industrial, Integración de Sistemas Críticos"
        }
    ],
    "experiencia": [
        {
            "empresa": "Atom Controles",
            "puesto": "Solutions Architect & Fundador",
            "periodo": "2013 - Actualidad",
            "puntos_clave": [
                "Diseño e implementación de sistemas de control para operaciones de misión crítica.",
                "Desarrollo e integración de arquitecturas multi-agente con LLMs para gestión de conocimiento."
            ]
        }
    ],
    "educacion": [
        {
            "institucion": "TripleTen",
            "titulo": "Bootcamp de Ciencia de Datos",
            "periodo": "2025 - 2026",
            "detalles": "Especialización en Machine Learning, Estadística y Análisis de Datos con Python."
        }
    ],
    "logro_destacado": {
        "titulo": "Sistema de Gestión de Conocimiento con IA",
        "desafio": "Pérdida de contexto en modelos de lenguaje tradicionales durante interacciones complejas.",
        "solucion": "Diseño de una arquitectura jerárquica de agentes con capas de contexto gobernadas centralmente.",
        "resultado": "Sistema operativo en producción con gestión autónoma de múltiples dominios."
    },
    "palabras_clave": [
        "Python", "Agentic AI", "Context Engineering", "Docker", "Machine Learning", "Systems Thinking"
    ]
}

if __name__ == "__main__":
    print("Iniciando prueba de generación de PDF...")
    try:
        # Nota: Para probarlo localmente sin el contenedor, ajustamos temporalmente la salida a la carpeta del servidor
        ruta_pdf = generar_cv(datos_de_prueba, nombre_archivo="CV_Test_Local_2.pdf")
        print(f"✅ ¡Éxito! PDF generado en: {ruta_pdf}")
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")