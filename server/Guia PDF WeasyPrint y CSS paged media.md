# Guía de Configuración Profesional de PDFs con WeasyPrint y CSS Paged Media

Esta guía técnica detalla la configuración avanzada de maquetación de documentos PDF profesionales en Python utilizando **WeasyPrint** y el estándar **CSS Paged Media (`@page`)**.

---

## 1. Módulos de Margen y Encabezados/Pies de Página

WeasyPrint divide cada página física en un contenedor central (*Page Area*) rodeado por 16 zonas o cajas de margen (*Margin Boxes*). Las cajas de margen permiten ubicar encabezados, pies de página, marcas de agua y numeración dinámica de forma independiente al flujo del HTML.

### Mapa de Zonas de Margen (`@page`)

\```text
+-------------------------------------------------------------------------+
|                               @top-left-corner                          |
| @top-left                     @top-center                    @top-right |
|                               @top-right-corner                         |
+-------------------------------------------------------------------------+
| @left-top     |                                         | @right-top    |
|               |                                         |               |
| @left-middle  |                PÁGINA                   | @right-middle |
|               |              (Page Area)                |               |
| @left-bottom  |                                         | @right-bottom |
+-------------------------------------------------------------------------+
|                            @bottom-left-corner                          |
| @bottom-left                @bottom-center                @bottom-right |
|                            @bottom-right-corner                         |
+-------------------------------------------------------------------------+
\```

---

## 2. Configuración CSS Paso a Paso

### Regla Base de Impresión y Variables Globales

Para garantizar la precisión de color, tipografía e impresión en hoja tamaño Carta (*Letter*), define los márgenes superiores e inferiores dejando espacio para los encabezados y pies de página:

\```css
@page {
    size: letter;
    margin-top: 28mm;    /* Reserva espacio para @top-* */
    margin-bottom: 22mm; /* Reserva espacio para @bottom-* */
    margin-left: 18mm;
    margin-right: 18mm;

    /* Encabezado Superior Izquierdo: Título/Sección */
    @top-left {
        content: "CARLOS ALBERTO JIMÉNEZ HIRASHI";
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 8pt;
        font-weight: 700;
        color: #0891b2; /* Cyan-600 */
        letter-spacing: 0.5px;
    }

    /* Encabezado Superior Derecho: Línea Decorativa Superior */
    @top-right {
        content: "DOCUMENTO TÉCNICO OFICIAL";
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 7.5pt;
        font-weight: 600;
        color: #64748b; /* Slate-500 */
    }

    /* Pie de Página Izquierdo: Aviso de Confidencialidad */
    @bottom-left {
        content: "Propiedad e Información Confidencial";
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 7.5pt;
        color: #94a3b8; /* Slate-400 */
        font-style: italic;
    }

    /* Pie de Página Derecho: Numeración Dinámica */
    @bottom-right {
        content: "Página " counter(page) " de " counter(pages);
        font-family: 'Helvetica', 'Arial', sans-serif;
        font-size: 8pt;
        font-weight: 600;
        color: #0e7490; /* Cyan-700 */
    }
}
\```

---

## 3. Omitir Encabezados/Pies en la Primera Página (`@page :first`)

Para documentos ejecutivos, informes o portadas donde la primera página debe lucir despejada (sin encabezados ni numeración), se aplica la pseudoclase `:first`:

\```css
/* Regla específica que sobrescribe la primera página */
@page :first {
    margin-top: 18mm; /* Margen superior estándar */
    
    /* Se limpian todas las cajas de margen en la portada/página 1 */
    @top-left { content: none; }
    @top-right { content: none; }
    @bottom-left { content: none; }
    @bottom-right { content: none; }
}
\```

---

## 4. Inserción de Marcas de Agua e Imágenes de Fondo

En WeasyPrint es perfectamente posible incluir **marcas de agua** (imágenes o vectores como logotipos, sellos de confidencialidad o marcas de fondo) en todas las hojas.

### Opción A: Marca de Agua vía CSS `@page` (Recomendada)

Puedes asignar un fondo directamente a la regla `@page`. De esta manera, la imagen de fondo abarca incluso las zonas de margen sin afectar el flujo del HTML:

\```css
@page {
    size: letter;
    margin: 25mm 18mm 20mm 18mm;
    
    /* Marca de agua centrada en toda la hoja */
    background-image: url('assets/watermark_logo.svg'); /* O PNG transparente */
    background-position: center center;
    background-repeat: no-repeat;
    background-size: 350px auto; /* Escala del logotipo */
    
    /* Nota: Si el archivo PNG no tiene opacidad nativa, prepáralo al 10%-15% de opacidad */
}
\```

### Opción B: Marca de Agua con Texto Vectorial en HTML/CSS

Si prefieres generar un texto de marca de agua oblicuo (ej. "CONFIDENCIAL" o "BORRADOR") sin usar imágenes externas:

#### HTML:
\```html
<div class="watermark-text">CONFIDENCIAL</div>
\```

#### CSS:
\```css
.watermark-text {
    position: fixed;
    top: 35%;
    left: 10%;
    width: 80%;
    text-align: center;
    font-size: 55pt;
    font-weight: 800;
    color: rgba(8, 145, 178, 0.06); /* Cyan-600 con 6% de opacidad */
    transform: rotate(-35deg);
    text-transform: uppercase;
    letter-spacing: 5px;
    z-index: -1000; /* Se renderiza por detrás de todo el contenido */
}
\```

---

## 5. Estructuras Visuales Avanzadas y Formas Geométricas

### Líneas Separadoras en Encabezados (`border-bottom`)

Para dar un acabado corporativo de alto nivel, se pueden añadir bordes inferiores a las cajas de margen superiores:

\```css
@page {
    @top-left {
        content: "SISTEMAS DE INFORMACIÓN Y ML";
        border-bottom: 1.5pt solid #0891b2; /* Línea de acento Cyan-600 */
        padding-bottom: 3px;
    }
    @top-right {
        content: "2026";
        border-bottom: 1.5pt solid #0891b2;
        padding-bottom: 3px;
    }
}
\```

### Numeración Distinta en Páginas Pares e Impares (`@page :left` y `@page :right`)

Para maquetar documentos tipo libro o reportes impresos a doble cara:

\```css
/* Páginas Impares (Derecha) */
@page :right {
    @bottom-right {
        content: "Página " counter(page);
    }
}

/* Páginas Pares (Izquierda) */
@page :left {
    @bottom-left {
        content: "Página " counter(page);
    }
}
\```

---

## 6. Integración en el Servidor MCP (Python)

Asegúrate de que la función que invoca WeasyPrint pase correctamente el parámetro `base_url` para que resuelva rutas de imágenes, fuentes CSS y marcas de agua relativas a la carpeta `templates`:

\```python
from weasyprint import HTML

def generar_documento_profesional(html_content: str, ruta_salida_pdf: str, templates_dir: str):
    # base_url le permite a WeasyPrint localizar imágenes de fondo o fuentes locales
    HTML(string=html_content, base_url=templates_dir).write_pdf(ruta_salida_pdf)
\```

---

## Resumen de Buenas Prácticas
1. **Control de Márgenes**: Mantén los márgenes `@page` superiores/inferiores (`25mm` a `30mm`) más amplios que los laterales (`15mm` a `18mm`) para dejar espacio libre a las cajas `@top-*` y `@bottom-*`.
2. **Formato Vectorial**: Utiliza logotipos en formato `.svg` o `.png` con transparencia de 8-bit para evitar bordes pixelados en impresión.
3. **Optimización de Color**: Utiliza valores hexadecimales o sintaxis `rgba()` para controlar la transparencia de marcas de agua directamente en el código.