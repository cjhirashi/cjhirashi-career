# PDF Generator Service

FastAPI-based microservice for generating professional PDF documents (CVs and Cover Letters) on-demand.

## Overview

**PDF Generator** is a high-performance, memory-efficient service that generates PDF documents in real-time without storing files on disk. It's designed to integrate seamlessly with the Portafolio-cjhirashi system's Admin Panel.

### Key Features

- **In-Memory Generation**: PDFs are generated in memory and streamed directly to clients
- **Two Document Types**: CV and Cover Letter templates with professional styling
- **Input Validation**: Robust Pydantic validation for all incoming data
- **Fast Performance**: Generates PDFs in under 5 seconds
- **Security**: Only accessible from Admin Panel (port 8002) via internal network
- **Logging & Monitoring**: Comprehensive logging for debugging and monitoring
- **Health Checks**: Built-in health check endpoint for container orchestration

## Architecture

### Technology Stack

- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn 0.24.0
- **PDF Generation**: ReportLab 4.0.7
- **Validation**: Pydantic 2.5.0
- **Testing**: Pytest 7.4.3 with pytest-cov
- **Python**: 3.11 (Alpine)

### Project Structure

```
pdf-generator/
├── src/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration and settings
│   ├── models.py            # Pydantic request/response schemas
│   ├── templates/
│   │   ├── cv_template.py   # CV PDF template
│   │   └── cover_letter_template.py  # Cover Letter template
│   ├── services/
│   │   ├── pdf_service.py   # Low-level PDF operations
│   │   ├── cv_generator.py  # CV generation logic
│   │   └── cover_letter_generator.py  # Cover Letter logic
│   ├── routes/
│   │   └── generate.py      # API endpoints
│   └── utils/
│       ├── validators.py    # Input validation
│       └── formatters.py    # Data formatting
├── tests/
│   ├── unit/
│   │   ├── test_cv_generator.py
│   │   └── test_cover_letter_generator.py
│   ├── integration/
│   │   ├── test_generate_cv_endpoint.py
│   │   └── test_generate_cover_letter_endpoint.py
│   └── fixtures/
│       └── sample_data.py   # Test data
├── Dockerfile
├── requirements.txt
├── pytest.ini
└── README.md
```

## API Endpoints

### Health Check

```http
GET /health
```

Returns service health status.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "service": "PDF Generator",
  "version": "1.0.0"
}
```

### Generate CV

```http
POST /generate/cv
```

Generates a professional CV PDF from career data.

**Request Body**:
```json
{
  "name": "Carlos Jiménez Hirashi",
  "email": "cjhirashi@gmail.com",
  "phone": "+34 666 777 888",
  "location": "Madrid, Spain",
  "ikigai": "Professional mission statement...",
  "about": "Professional bio...",
  "competencies": [
    {
      "category": "Programming Languages",
      "name": "Python",
      "level": "Expert"
    }
  ],
  "experience": [
    {
      "position": "Senior Backend Engineer",
      "company": "Company X",
      "startDate": "2022-01",
      "endDate": "present",
      "description": "Responsibilities and achievements..."
    }
  ],
  "education": [
    {
      "degree": "Master's Degree",
      "school": "University Name",
      "field": "Computer Science",
      "year": "2020"
    }
  ],
  "projects": [
    {
      "name": "Project Name",
      "description": "Project description...",
      "technologies": ["Python", "FastAPI"],
      "link": "https://github.com/project"
    }
  ]
}
```

**Response** (200 OK):
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="CV_CarlosJimenez.pdf"`
- Body: Binary PDF data

**Error Responses**:
- 400 Bad Request: Validation error with detail message
- 500 Internal Server Error: PDF generation failure

### Generate Cover Letter

```http
POST /generate/cover-letter
```

Generates a professional Cover Letter PDF.

**Request Body**:
```json
{
  "name": "Carlos Jiménez Hirashi",
  "email": "cjhirashi@gmail.com",
  "date": "2024-08-16",
  "companyName": "Target Company Inc.",
  "companyAddress": "123 Business Ave, City, State",
  "recipientName": "Hiring Manager",
  "position": "Senior Software Engineer",
  "body": "Letter body content with multiple paragraphs...",
  "closingStatement": "I look forward to discussing...",
  "signature": "Carlos Jiménez Hirashi"
}
```

**Response** (200 OK):
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="CoverLetter_CarlosJimenez_TargetCompany.pdf"`
- Body: Binary PDF data

**Error Responses**:
- 400 Bad Request: Validation error
- 500 Internal Server Error: PDF generation failure

## Installation & Setup

### Local Development

1. Create Python virtual environment:
```bash
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run development server:
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8080 --reload
```

4. API documentation available at: `http://localhost:8080/docs`

### Docker

Build and run with Docker:

```bash
# Build image
docker build -t pdf-generator:latest .

# Run container
docker run -p 8080:8080 pdf-generator:latest
```

## Testing

### Run All Tests

```bash
pytest
```

### Run with Coverage Report

```bash
pytest --cov=src --cov-report=html
```

Coverage report will be generated in `htmlcov/index.html`.

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Tests matching pattern
pytest -k "cv" -v
```

### Current Coverage

- Target: 80%+ coverage
- Generated reports: `htmlcov/` directory after running tests

## Configuration

Create `.env` file in the project root (optional):

```env
# Application
DEBUG=false
LOG_LEVEL=INFO

# PDF Generation
PDF_TIMEOUT_SECONDS=30
MAX_PDF_SIZE_MB=50
```

Default values are used if `.env` is not provided.

## Performance

### Generation Time

- CV: < 5 seconds (typical: 2-3 seconds)
- Cover Letter: < 3 seconds (typical: 1-2 seconds)

### Memory Usage

- Per request: < 50MB
- Supports concurrent requests

### Optimization

- In-memory streaming (no disk I/O)
- Efficient BytesIO buffering
- Stream response directly to client

## Integration with Admin Panel

### Connection Details

- **Service**: PDF Generator
- **Host**: `pdf-generator` (internal Docker network)
- **Port**: 8080 (internal, not exposed)
- **Network**: `network-cjhirashi-srv`
- **Access**: ONLY from Admin Panel (port 8002)

### Usage from Admin Panel

From Admin Panel, make requests to:

```
http://pdf-generator:8080/generate/cv
http://pdf-generator:8080/generate/cover-letter
```

Example fetch call in JavaScript:

```javascript
const cvData = { /* career data */ };

const response = await fetch('http://pdf-generator:8080/generate/cv', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(cvData)
});

const blob = await response.blob();
const url = window.URL.createObjectURL(blob);
const a = document.createElement('a');
a.href = url;
a.download = 'CV_CarlosJimenez.pdf';
a.click();
```

## Design Decisions

### In-Memory Generation (SOLID - Single Responsibility)

PDFs are generated in memory and streamed to clients without storing on disk:

- **Advantages**: No disk I/O latency, improved security, automatic cleanup
- **Disadvantage**: Requires sufficient memory for concurrent requests
- **Trade-off**: Memory usage acceptable for typical concurrent load (< 100 requests)

### ReportLab over WeasyPrint

Chose ReportLab for PDF generation:

- **Advantages**: Smaller memory footprint, no external dependencies, faster startup
- **Disadvantage**: Less CSS-based styling (trade-off acceptable)

### Separated Templates and Generators

- `templates/`: Pure PDF layout and rendering logic
- `services/`: Business logic for data preparation and generation orchestration
- **Benefit**: Easy to swap templates or add new document types

### Comprehensive Validation

- Pydantic schemas at API boundary for automatic validation
- Custom validators for complex business rules
- Sanitizers for PDF security

## Error Handling

### Validation Errors (400)

Invalid input data triggers validation errors with descriptive messages:

```json
{
  "detail": "Name is required"
}
```

### Generation Errors (500)

PDF generation failures return 500 with detail:

```json
{
  "detail": "Error generating CV"
}
```

### Logging

All operations logged to stdout with timestamps and levels:

```
2024-08-16 10:30:45 - src.routes.generate - INFO - Processing CV generation request for Carlos Jiménez Hirashi
2024-08-16 10:30:46 - src.services.cv_generator - INFO - CV generated successfully for Carlos Jiménez Hirashi
```

## Security Considerations

- **Network Isolation**: Only accessible from Admin Panel via internal Docker network
- **Input Validation**: All fields validated against strict Pydantic schemas
- **No Data Storage**: PDFs generated in memory, never written to disk
- **No File System Access**: Service runs without file system write permissions
- **Security Context**: Container runs as non-root user `appuser`
- **No Secrets**: No sensitive data stored or logged

## Troubleshooting

### PDFs Too Large

If generated PDFs are unexpectedly large:

1. Check content length in logs
2. Verify images/embedded content isn't bloating file
3. Monitor memory usage during generation

### Timeouts

If generation takes > 30 seconds:

1. Check system resources (CPU, memory)
2. Review data size (large projects/experience lists)
3. Increase `PDF_TIMEOUT_SECONDS` if needed

### Memory Leaks

If memory grows unbounded:

1. Check logs for errors during generation
2. Monitor container memory limits
3. Verify BytesIO cleanup after streaming response

## Development Workflow

1. **Write Tests First**: Create tests in `tests/` before implementing features
2. **SOLID Principles**: Keep single responsibility in each module
3. **Clean Code**: Follow PEP 8 style guide
4. **Document**: Add docstrings to all functions
5. **Test Coverage**: Maintain 80%+ coverage

## Deployment

### Docker Compose Integration

Service is configured in main `docker-compose.yml`:

```yaml
pdf_generator:
  build:
    context: ./pdf-generator
    dockerfile: Dockerfile
  container_name: pdf_generator
  restart: unless-stopped
  networks:
    - network-cjhirashi-srv
  depends_on:
    - api_rest
  healthcheck:
    test: ["CMD", "wget", "-qO-", "http://localhost:8080/health"]
    interval: 30s
    timeout: 5s
    retries: 3
```

### Health Checks

Container includes health check endpoint that:

- Returns 200 status if service is healthy
- Used by Docker to monitor service status
- Automatically restarts if unhealthy

## Future Enhancements

- [ ] Support additional document templates (e.g., Resumé variations)
- [ ] Custom styling/theme configuration
- [ ] Resume-specific features (skills categorization, ATS compatibility)
- [ ] Batch PDF generation endpoint
- [ ] PDF preview endpoint (low-resolution)
- [ ] Internationalization support

## License

Part of Portafolio-cjhirashi project.

## Support

For issues or questions, refer to the main project documentation.
