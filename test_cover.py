import os
from tools.cover_generator import generar_cover_letter

datos_prueba_cover = {
    "encabezado": {
        "nombre": "Carlos Alberto Jiménez Hirashi",
        "email": "cjhirashi@gmail.com",
        "ubicacion": "CDMX, México",
        "sitio_web": "cjhirashi.com",
        "github": "github.com/cjhirashi"
    },
    "fecha": "12 de agosto de 2026",
    "empresa": "Cobalto Talent",
    "párrafos": [
        "Me dirijo a ustedes para postularme al rol de Data Scientist con enfoque en Machine Learning. Lo que me atrae de esta posición no es solo el stack técnico, sino la oportunidad de trabajar en problemas de predicción donde un modelo mal diseñado tiene consecuencias reales, no solo un número de accuracy más bajo.",
        "Completé el Bootcamp de Ciencia de Datos de TripleTen (2025-2026) con siete proyectos end-to-end que cubren clasificación, regresión, A/B testing, análisis exploratorio y deployment: modelos de churn bancario (F1=0.611, AUC-ROC = 0.860), selección de regiones de extracción con análisis de riesgo estadístico vía bootstrapping, y optimización de recuperación de oro en proceso industrial con métrica personalizada SMAPE ponderada. Sin embargo, mi diferenciador real no es el bootcamp, es lo que llevo al análisis de datos desde 20 años de ingeniería en sistemas críticos.",
        "En automatización industrial aprendí que un sistema bien diseñado debe anticipar dónde va a fallar antes de construirlo, operar sin supervisión constante, y resistir condiciones que nadie planificó. Ese mismo principio lo aplico hoy al ML: audito la calidad de los datos antes de procesar, valido la integridad del pipeline antes de entrenar, y diseño modelos que generalizan en producción, no solo en el set de prueba. El caso que mejor lo ilustra: rediseñé los controles de un laboratorio de bioseguridad gubernamental en Colombia que una consultora internacional no había logrado resolver. El sistema superó el nivel de certificación requerido a la primera, el mismo estándar que aplico a cualquier entrega técnica.",
        "Me interesa explorar cómo puedo contribuir al equipo de Cobalto Talent. Estoy disponible para una conversación cuando sea conveniente para ustedes."
    ]
}

if __name__ == "__main__":
    print("Iniciando generación de Cover Letter de prueba...")
    try:
        ruta_salida = generar_cover_letter(datos_prueba_cover, "CoverLetter_Test_2.pdf")
        print(f"✅ ¡Cover Letter generada con éxito en!: {ruta_salida}")
    except Exception as e:
        print(f"❌ Error al generar Cover Letter: {e}")