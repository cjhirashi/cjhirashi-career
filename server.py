import json
from mcp.server.fastmcp import FastMCP
from tools.cv_generator import generar_cv

mcp = FastMCP("MCP-Tools-Server", host="0.0.0.0", port=8000)

@mcp.tool()
def crear_cv_pdf(datos_cv_json: str, nombre_archivo: str = "CV_Documento.pdf") -> str:
    """
    Genera un CV profesional en PDF recibiendo una cadena JSON formateada según la estructura acordada.
    Guarda el resultado en la carpeta de salidas persistentes del servidor.
    """
    try:
        datos = json.loads(datos_cv_json)
        ruta_resultado = generar_cv(datos, nombre_archivo)
        return f"Éxito: PDF generado correctamente en '{ruta_resultado}'"
    except Exception as e:
        return f"Error generando PDF: {str(e)}"

if __name__ == "__main__":
    mcp.run(transport="sse")