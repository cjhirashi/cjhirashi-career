import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

def generar_cover_letter(datos: dict, nombre_archivo: str = "CoverLetter_Documento.pdf") -> str:
    # Rutas absolutas
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    templates_dir = os.path.join(base_dir, "templates")
    directorio_salida = "/mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters"
    
    # Crear subcarpeta /cover_letters si no existe
    os.makedirs(directorio_salida, exist_ok=True)
    ruta_salida_completa = os.path.join(directorio_salida, nombre_archivo)
    
    # Cargar plantilla Jinja2
    env = Environment(loader=FileSystemLoader(templates_dir))
    template = env.get_template("cover_template.html")
    html_out = template.render(**datos)
    
    # WeasyPrint resuelve el CSS global usando base_url
    HTML(string=html_out, base_url=templates_dir).write_pdf(ruta_salida_completa)
    
    return ruta_salida_completa