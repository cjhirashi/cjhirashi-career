import json
from fastmcp import FastMCP
from tools.cv_generator import generar_cv
from tools.cover_generator import generar_cover_letter

# Instanciación limpia requerida por la versión reciente de FastMCP
mcp = FastMCP("MCP-Tools-Server")


@mcp.tool()
def crear_cv_pdf(
    datos_cv_json: str, nombre_archivo: str = "CV_Documento.pdf"
) -> str:
  """Genera un CV profesional en PDF recibiendo una cadena JSON formateada según la estructura acordada.

  Guarda el resultado en la carpeta de salidas persistentes del servidor
  (/mcp-outputs/cvs).
  """
  try:
    datos = json.loads(datos_cv_json)
    ruta_resultado = generar_cv(datos, nombre_archivo)
    return f"Éxito: PDF generado correctamente en '{ruta_resultado}'"
  except Exception as e:
    return f"Error generando PDF: {str(e)}"


@mcp.tool()
def crear_cover_letter_pdf(
    datos_cover_json: str, nombre_archivo: str = "CoverLetter_Documento.pdf"
) -> str:
  """Genera una Carta de Presentación (Cover Letter) profesional en PDF recibiendo una cadena JSON formateada.

  Guarda el resultado en la carpeta de salidas persistentes del servidor
  (/mcp-outputs/cover_letters).
  """
  try:
    datos = json.loads(datos_cover_json)
    ruta_resultado = generar_cover_letter(datos, nombre_archivo)
    return f"Éxito: PDF generado correctamente en '{ruta_resultado}'"
  except Exception as e:
    return f"Error generando PDF: {str(e)}"


if __name__ == "__main__":
  # El transporte SSE y la configuración de red
  mcp.run(transport="sse", host="0.0.0.0", port=8000)