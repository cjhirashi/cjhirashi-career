# MCP PDF Generator Server

Servidor MCP (Model Context Protocol) desarrollado en Python para la generación automatizada de documentos en formato PDF de alta calidad profesional (CVs, Cartas de Presentación, Reportes) utilizando **Jinja2** como motor de plantillas HTML y **WeasyPrint** para la renderización CSS/Paged Media.

---

## 🛠️ Requisitos Previos e Instalación de Dependencias

### 1. Dependencias de Sistema (Ubuntu / Linux)

WeasyPrint requiere librerías nativas de renderizado de fuentes y gráficos C. Ejecuta el siguiente comando en tu servidor:

\```bash
sudo apt update && sudo apt install -y \
  build-essential \
  python3-dev \
  libpangocairo-1.0-0 \
  libpango-1.0-0 \
  libcairo2 \
  libgdk-pixbuf-2.0-0 \
  libffi-dev \
  shared-mime-info \
  fonts-liberation
\```

### 2. Entorno Virtual de Python con Pipenv

Instala las dependencias del proyecto especificadas en el `Pipfile`:

\```bash
pipenv install
\```

Las librerías principales utilizadas son:
* `mcp`: Protocolo de integración para Model Context Protocol.
* `jinja2`: Renderizado de plantillas HTML dinámicas.
* `weasyprint`: Compilación de HTML/CSS a PDF comercial.

---

## 📂 Estructura del Proyecto

```text
mcp-server/
├── templates/
│   ├── css/
│   │   └── style_1.css          # Hoja de estilos global (Paleta Cyan-600)
│   ├── cv_template.html         # Plantilla HTML para Curriculum Vitae
│   └── cover_template.html      # Plantilla HTML para Cover Letter
├── tools/
│   ├── cv_generator.py          # Módulo Python para generación de CVs
│   └── cover_generator.py       # Módulo Python para generación de Cover Letters
├── Pipfile
├── Pipfile.lock
├── test.py                      # Script de prueba para CV
├── test_cover.py                # Script de prueba para Cover Letter
└── README.md
```

---

## 🚀 Uso y Pruebas Locales

Antes de ejecutar los scripts, asegúrate de activar el entorno virtual:

```bash
pipenv shell
```

### 1. Probar Generación de Curriculum Vitae (CV)

Ejecuta el script de prueba para generar un CV en PDF:

```bash
python test_cv.py
```

El PDF generado se depositará automáticamente en:
`/mnt/disco2/cjhirashi-data/mcp-outputs/cvs/CV_Documento.pdf`

### 2. Probar Generación de Cover Letter

Ejecuta el script de prueba para la carta de presentación:

```bash
python test_cover.py
```

El PDF generado se depositará automáticamente en:
`/mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/CoverLetter_Test.pdf`

---

## 🌐 Previsualización Rápida vía HTTP

Para visualizar o descargar los PDFs creados desde cualquier navegador web en tu red local sin depender de herramientas externas, puedes desplegar el servidor HTTP nativo de Python:

### Para ver los documentos:
\```bash
python3 -m http.server 8080 --directory /mnt/disco2/cjhirashi-data/mcp-outputs
\```

#### Para los CVs
Accede desde tu navegador a: `http://<IP-DE-TU-SERVIDOR>:8080/cvs/CV_Documento.pdf`

#### Para los CoverLetters
Accede desde tu navegador a: `http://<IP-DE-TU-SERVIDOR>:8080/cover_letters/CoverLetter_Test.pdf`

*(Presiona `Ctrl + C` en la terminal para apagar el servidor temporal una vez revisado).*

---

## ⚙️ Rutas de Salida Organizadas

Todos los artefactos generados por el servidor se canalizan a la estructura centralizada de almacenamiento:

* **Directorio Raíz de Salidas:** `/mnt/disco2/cjhirashi-data/mcp-outputs/`
* **Módulo CVs:** `/mnt/disco2/cjhirashi-data/mcp-outputs/cvs/`
* **Módulo Cover Letters:** `/mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/`