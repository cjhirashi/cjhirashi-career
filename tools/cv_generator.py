import os
import json
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def generar_cv(datos: dict, nombre_archivo: str = "CV_Documento.pdf") -> str:
    # Definir rutas absolutas dentro del contenedor
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(base_dir, "templates")
    directorio_salida = "/mnt/disco2/cjhirashi-data/mcp-outputs/cvs"
    
    os.makedirs(directorio_salida, exist_ok=True)
    ruta_salida_completa = os.path.join(directorio_salida, nombre_archivo)
    
    # Cargar plantilla desde Jinja2
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("cv_template.html")
    html_out = template.render(**datos)
    
    # WeasyPrint resuelve el CSS pasando templates_dir como base_url
    HTML(string=html_out, base_url=templates_dir).write_pdf(ruta_salida_completa)
    
    return ruta_salida_completa