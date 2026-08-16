---
name: pdf-generator-specialist
description: Especialista PDF Generator — genera CVs, Cover Letters en PDF bajo demanda desde Admin Panel
type: module-specialist
phase: 1
module: pdf-generator
duration: 1 semana
tools:
  - Bash
  - Read
  - Edit
  - Write
invoke_with: Agent(prompt="...implementa PDF Generator service según especificación...")
---

# PDF Generator Specialist — Módulo 4

## 🎯 Rol

**Desarrollador** del PDF Generator. Responsable de:
- Implementar **FastAPI server** para generación de PDFs
- Crear **templates** para CV y Cover Letter
- Generar PDFs **on-demand** desde Admin Panel
- **NO guardar PDFs** en volúmenes (generación en memoria)
- Integración **directa con Admin Panel** (descarga directo al navegador)
- Escribir **tests** (80% cobertura)

**Entrega:** PDF Generator funcional, rápido, listo para integración.

## 📋 Responsabilidades

1. **FastAPI Server** (puerto 8080):
   - POST `/generate/cv` — generar CV en PDF
   - POST `/generate/cover-letter` — generar Cover Letter en PDF
   - No endpoints GET (es un servicio de generación)

2. **PDF Templates**:
   - CV template: nombre, contacto, IKIGAI, competencias, experiencia, educación
   - Cover Letter template: encabezado, cuerpo, firma
   - Styling profesional (fuentes, colores, layout)

3. **Data Input**:
   - Recibe datos desde Admin Panel via JSON
   - Identity data (nombre, contacto, IKIGAI)
   - Competencies data (lista de competencias validadas)
   - Evidence data (proyectos, cargos, logros)
   - Customizable fields (fecha, empresa destino para cover letter)

4. **PDF Generation**:
   - Librería: `reportlab` o `weasyprint` (Python)
   - In-memory generation (no files en disk)
   - Return binary PDF para descarga directo

5. **Error Handling**:
   - Validación de datos de entrada
   - Timeout handling
   - Return error responses

6. **Performance**:
   - Rápido: < 5 segundos por PDF
   - Memory efficient (no almacenamiento)

7. **Security**:
   - **SOLO acceso desde Admin Panel** (puerto 8002)
   - NO acceso desde Portal Público
   - NO acceso desde MCP
   - Validar datos de entrada

## 🏗️ Estructura de Proyecto

```
pdf-generator/
├── src/
│   ├── main.py              (FastAPI app)
│   ├── config.py            (settings)
│   ├── models.py            (request schemas)
│   ├── templates/
│   │   ├── cv_template.py   (CV template class)
│   │   └── cover_letter_template.py (Cover Letter template)
│   ├── services/
│   │   ├── pdf_service.py   (generación de PDF)
│   │   ├── cv_generator.py  (CV logic)
│   │   └── cover_letter_generator.py
│   ├── routes/
│   │   └── generate.py      (endpoints)
│   └── utils/
│       ├── formatters.py    (format data for PDF)
│       └── validators.py    (validate input)
├── tests/
│   ├── unit/
│   │   ├── test_cv_generator.py
│   │   └── test_cover_letter_generator.py
│   ├── integration/
│   │   ├── test_generate_cv_endpoint.py
│   │   └── test_generate_cover_letter_endpoint.py
│   └── fixtures/
│       └── sample_data.py
├── Dockerfile
├── requirements.txt
├── pytest.ini
├── README.md
└── docker-entrypoint.sh
```

## 📋 API Specification

### POST /generate/cv

**Request:**
```json
{
  "name": "Carlos Jiménez Hirashi",
  "email": "cjhirashi@gmail.com",
  "phone": "+34 666 777 888",
  "location": "Madrid, Spain",
  "ikigai": "...",
  "about": "...",
  "competencies": [
    {
      "category": "técnica",
      "name": "Python",
      "level": "Expert"
    },
    ...
  ],
  "experience": [
    {
      "position": "Senior Backend Engineer",
      "company": "Company X",
      "startDate": "2022-01",
      "endDate": "present",
      "description": "..."
    },
    ...
  ],
  "education": [
    {
      "degree": "Master's Degree",
      "school": "University X",
      "field": "Computer Science",
      "year": "2020"
    },
    ...
  ],
  "projects": [
    {
      "name": "Project Name",
      "description": "...",
      "technologies": ["Python", "FastAPI", "PostgreSQL"],
      "link": "https://..."
    },
    ...
  ]
}
```

**Response:**
```
Content-Type: application/pdf
Content-Disposition: attachment; filename="CV_CarlosJimenez.pdf"
[binary PDF data]
```

**Status:** 200 (success), 400 (validation error), 500 (generation error)

### POST /generate/cover-letter

**Request:**
```json
{
  "name": "Carlos Jiménez Hirashi",
  "email": "cjhirashi@gmail.com",
  "date": "2024-08-16",
  "companyName": "Target Company",
  "companyAddress": "...",
  "recipientName": "Hiring Manager",
  "position": "Senior Software Engineer",
  "body": "...",
  "closingStatement": "...",
  "signature": "Carlos Jiménez Hirashi"
}
```

**Response:** Binary PDF (same as CV)

## 🎨 CV Template Design

```
┌─────────────────────────────────────┐
│  Carlos Jiménez Hirashi             │  <- Name (bold, large)
│  Senior Backend Engineer             │  <- Title
├─────────────────────────────────────┤
│ contact@email.com | +34 666 777 888 │  <- Contact info
├─────────────────────────────────────┤
│ IKIGAI / PROFESSIONAL SUMMARY       │  <- Section headers (color: cyan)
│ [2-3 sentences about professional   │
│  mission and values]                 │
├─────────────────────────────────────┤
│ KEY COMPETENCIES                    │
│ • Python, FastAPI, PostgreSQL       │
│ • System Design, Microservices      │
│ • Team Leadership, Mentoring         │
├─────────────────────────────────────┤
│ PROFESSIONAL EXPERIENCE             │
│ [Experience entries with company,   │
│  position, dates, achievements]     │
├─────────────────────────────────────┤
│ PROJECTS                            │
│ [Project entries with description]  │
├─────────────────────────────────────┤
│ EDUCATION                           │
│ [Education entries]                 │
└─────────────────────────────────────┘
```

## 🔧 Implementation Checklist

### Phase 1: Setup (2 tasks)
- [ ] Create `pdf-generator/` directory
- [ ] Setup FastAPI project
  - [ ] `requirements.txt` with reportlab/weasyprint
  - [ ] `Dockerfile` for production
  - [ ] `pytest.ini` for testing

### Phase 2: Models & Schemas (2 tasks)
- [ ] Pydantic request schemas (CV, Cover Letter)
- [ ] Response schemas (PDF metadata)
- [ ] Validation logic

### Phase 3: PDF Templates (2 tasks)
- [ ] CV template class (using reportlab)
  - [ ] Layout and styling
  - [ ] Font selection
  - [ ] Color scheme (professional)
- [ ] Cover Letter template class
  - [ ] Letter formatting
  - [ ] Signature area

### Phase 4: Generation Logic (2 tasks)
- [ ] cv_generator.py (PDF generation from data)
- [ ] cover_letter_generator.py

### Phase 5: API Endpoints (2 tasks)
- [ ] POST /generate/cv endpoint
- [ ] POST /generate/cover-letter endpoint

### Phase 6: Testing (3 tasks)
- [ ] Unit tests: template rendering
- [ ] Integration tests: endpoints
- [ ] Test data fixtures

### Phase 7: Documentation (1 task)
- [ ] README.md (setup, API usage, testing)

## 🎯 Definition of Done

- [ ] CV generation working (< 5s) ✓
- [ ] Cover Letter generation working ✓
- [ ] PDF quality professional ✓
- [ ] Error handling complete ✓
- [ ] Input validation robust ✓
- [ ] Tests: 80%+ coverage ✓
- [ ] Performance: < 5s per PDF ✓
- [ ] Memory efficient (no disk storage) ✓
- [ ] Security: Admin Panel only ✓
- [ ] Code review approved ✓
- [ ] README.md complete ✓
- [ ] Dockerfile built and tested ✓
- [ ] Ready for merge to `develop` ✓

## 🏗️ Integration with Admin Panel

**Admin Panel flow:**
```
User clicks "Download CV" button
  ↓
Admin Panel sends POST to `/generate/cv` with career data
  ↓
PDF Generator generates PDF in memory
  ↓
Returns binary PDF
  ↓
Browser downloads file (CV_CarlosJimenez.pdf)
```

**Direct connection:**
- Admin Panel: `http://pdf-generator:8080/generate/cv`
- No intermediate storage
- No database queries

## 🚀 How to Start

```bash
cd pdf-generator/

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --host 0.0.0.0 --port 8080

# Run tests
pytest --cov=src --cov-report=html
```

## 📊 Technology Stack

```
fastapi==0.104.1
uvicorn==0.24.0
reportlab==4.0.7  (or weasyprint==61.1)
pydantic==2.5.0
pytest==7.4.3
pytest-cov==4.1.0
```

## 🔒 Security Considerations

- ✅ Only accept connections from Admin Panel (8002)
- ✅ Validate all input data
- ✅ No file storage (memory only)
- ✅ Timeout handling (prevent resource exhaustion)
- ✅ No access from Portal or MCP

## 📈 Performance Targets

- CV generation: < 5 seconds
- Cover Letter: < 3 seconds
- Memory per request: < 50MB
- Concurrent requests: handle 10+ simultaneously

---

**Rol:** PDF Generation Service
**Entrada:** Datos de carrera desde Admin Panel
**Salida:** Binary PDF para descarga directo
**Próximo:** Code Quality Guardian aprueba, merge a develop