# Topología de Red — MCP Tools Server

_Configuración de red, puertos, volúmenes y conectividad del sistema._

## Diagrama de Topología General

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#A855F7',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#9333EA',
    'secondaryColor': '#10B981',
    'secondaryBorderColor': '#059669',
    'tertiaryColor': '#06B6D4',
    'tertiaryBorderColor': '#0891B2',
    'lineColor': '#059669',
    'fontSize': '13px'
  }
}}%%

graph TB
  subgraph external["🌐 Red Externa"]
    CLIENT["Cliente Web<br/>Navegador"]
  end

  subgraph host["🖥️ Host Machine"]
    PORT8002["Puerto 8002<br/>HTTP Listening"]
    MOUNT["Montaje Host<br/>/mnt/disco2/cjhirashi-data"]
    DIRS["mcp-outputs/<br/>├── cvs<br/>└── cover_letters"]
  end

  subgraph network["🔗 Docker Network"]
    BRIDGE["network-cjhirashi-srv<br/>Bridge Driver"]
  end

  subgraph container["🐳 Contenedor Docker"]
    CONT["mcp_tools_server<br/>Python 3.11 + FastMCP"]
    PORT8000["Puerto 8000<br/>Uvicorn"]
    APPDIR["App Directory<br/>/app"]
    VOLMOUNT["Volume Mount<br/>/app/outputs"]
  end

  CLIENT -->|"HTTP<br/>POST /sse"| PORT8002
  PORT8002 -->|"8002→8000"| PORT8000
  PORT8000 -->|"Escucha"| CONT
  CONT -->|"Red"| BRIDGE

  MOUNT <-->|"Bind Volume"| VOLMOUNT
  VOLMOUNT -->|"Escribe"| DIRS
  CONT -->|"Lee"| APPDIR

  classDef externalBg fill:#E0A5F7,stroke:#A855F7,stroke-width:2px,color:#fff
  classDef externalNode fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff
  classDef hostBg fill:#E5E7EB,stroke:#9CA3AF,stroke-width:2px,color:#333
  classDef hostNode fill:#D1D5DB,stroke:#6B7280,stroke-width:2px,color:#333
  classDef networkBg fill:#A7E8A7,stroke:#10B981,stroke-width:2px,color:#fff
  classDef networkNode fill:#10B981,stroke:#059669,stroke-width:2px,color:#fff
  classDef containerBg fill:#A5DEDA,stroke:#06B6D4,stroke-width:2px,color:#fff
  classDef containerNode fill:#06B6D4,stroke:#0891B2,stroke-width:2px,color:#fff

  class external externalBg
  class CLIENT externalNode
  class host hostBg
  class PORT8002,MOUNT,DIRS hostNode
  class network networkBg
  class BRIDGE networkNode
  class container containerBg
  class CONT,PORT8000,APPDIR,VOLMOUNT containerNode
```

## Configuración de Puertos

### Puerto Mapeado

| Dirección | Puerto Host | Puerto Contenedor | Protocolo | Uso |
|-----------|-------------|-------------------|-----------|-----|
| **Entrada** | 8002 | 8000 | HTTP | MCP Client → Uvicorn Server |
| **Escucha** | 0.0.0.0:8002 | 0.0.0.0:8000 | TCP | FastMCP Server |

### Explicación

- **Host 8002** ← Puerto expuesto en la máquina host
- **Contenedor 8000** ← Puerto interno donde escucha Uvicorn
- **Mapping**: `docker-compose.yml` define `ports: ["8002:8000"]`

```yaml
# docker-compose.yml
services:
  mcp_tools_server:
    ports:
      - "8002:8000"  # Host:Container
```

### Conexión desde Cliente

```
Cliente (navegador)
  ↓
http://localhost:8002/sse   (HTTP/SSE)
  ↓
Docker Port Mapping 8002→8000
  ↓
Uvicorn en 0.0.0.0:8000
  ↓
FastMCP Handler
```

---

## Configuración de Volúmenes

### Bind Volume: Host ↔ Contenedor

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7',
    'lineColor': '#059669'
  }
}}%%

graph LR
  HOST["Host<br/>/mnt/disco2<br/>cjhirashi-data<br/>mcp-outputs"]
  BIND["Bind Volume<br/>Sincronizado"]
  CONT["Contenedor<br/>/app/outputs"]
  PDF["pdf_file.pdf<br/>Persistente"]
  
  HOST <-->|"Lectura/Escritura"| BIND
  BIND <-->|"Montado en"| CONT
  CONT -->|"Escribe"| PDF
  PDF -->|"Accesible"| HOST
  
  style HOST fill:#E5E7EB,stroke:#9CA3AF,stroke-width:2px,color:#333
  style BIND fill:#10B981,stroke:#059669,stroke-width:2px,color:#fff
  style CONT fill:#06B6D4,stroke:#0891B2,stroke-width:2px,color:#fff
  style PDF fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff
```

### Configuración en docker-compose.yml

```yaml
volumes:
  # Bind volume: permite persistencia y acceso desde host
  - /mnt/disco2/cjhirashi-data/mcp-outputs:/app/outputs
```

### Estructura de Directorios

**En Host:**
```
/mnt/disco2/cjhirashi-data/
└── mcp-outputs/
    ├── cvs/                    ← CVs generados
    │   ├── cv_john_2026.pdf
    │   ├── cv_jane_2026.pdf
    │   └── ...
    └── cover_letters/          ← Cover letters generados
        ├── cover_john_2026.pdf
        ├── cover_jane_2026.pdf
        └── ...
```

**En Contenedor:**
```
/app/
├── outputs/                    ← Montaje de /mnt/disco2/.../mcp-outputs/
│   ├── cvs/
│   ├── cover_letters/
├── server.py
├── tools/
├── templates/
└── ...
```

### Ventajas del Bind Volume

1. **Persistencia**: PDFs permanecen después de reiniciar contenedor
2. **Acceso Host**: Fácil lectura desde la máquina host
3. **Backups**: Directorio en host = fácil de respaldar
4. **Permisos**: Controlados por sistema de archivos host
5. **Rendimiento**: Mejor que Docker named volumes para I/O intenso

---

## Red Docker

### Tipo de Red

```yaml
networks:
  network-cjhirashi-srv:
    driver: bridge
    external: true
```

**Bridge Network**: Red virtual que conecta contenedores entre sí y con el host.

### Características

| Característica | Valor |
|---|---|
| **Tipo** | Bridge (virtual) |
| **Controlador** | bridge |
| **Aislamiento** | Contenedores en la misma red se ven entre sí |
| **Acceso Host** | Vía localhost:8002 |
| **Externo** | `external: true` — Red creada externamente |

### Resolución de Nombres en la Red

```
Dentro de la red bridge:
- Nombre: mcp_tools_server
- Dirección IP: Dinámica (ej: 172.20.0.2)
- Accesible desde: Otros contenedores en la misma red
```

---

## Flujo de Solicitud HTTP

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#A855F7',
    'primaryTextColor': '#ffffff',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#06B6D4',
    'lineColor': '#059669'
  }
}}%%

sequenceDiagram
  participant BROWSER as 📱 Navegador
  participant HOSTNET as 🖥️ Host Network
  participant DOCKER as 🐳 Docker
  participant UVICORN as 🚀 Uvicorn
  participant APP as ⚙️ FastMCP

  BROWSER->>HOSTNET: TCP → :8002
  HOSTNET->>DOCKER: Forward 8002→8000
  DOCKER->>UVICORN: Conectar
  UVICORN->>APP: Request
  BROWSER->>APP: POST /sse crear_cv_pdf
  APP->>APP: Parsear JSON
  APP->>APP: Render Jinja2
  APP->>APP: WeasyPrint
  APP->>HOSTNET: Escribe /mcp-outputs/
  APP->>UVICORN: SSE Response
  UVICORN->>BROWSER: PDF Generado ✅
  BROWSER->>HOSTNET: GET archivo.pdf
  HOSTNET->>BROWSER: PDF (descarga)
```

---

## Configuración de docker-compose.yml

Archivo completo de orquestación:

```yaml
version: '3.8'

services:
  mcp_tools_server:
    # Imagen y construcción
    build:
      context: .
      dockerfile: Dockerfile
    image: mcp-server-mcp-tools:latest
    container_name: mcp_tools_server
    
    # Puertos expuestos
    ports:
      - "8002:8000"  # HTTP: Host:Container
    
    # Volúmenes (persistencia)
    volumes:
      - /mnt/disco2/cjhirashi-data/mcp-outputs:/app/outputs
      # Templates se pueden montar opcionalmente para hot-reload
      # - ./templates:/app/templates
    
    # Red
    networks:
      - network-cjhirashi-srv
    
    # Reinicio automático
    restart: unless-stopped
    
    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
    
    # Variables de entorno (opcionales)
    environment:
      - PYTHONUNBUFFERED=1
      - APP_ENV=production
    
    # Health check (propuesto)
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

networks:
  network-cjhirashi-srv:
    external: true
    driver: bridge
```

---

## Seguridad de Red

### Configuración Actual

| Aspecto | Actual | Riesgo |
|--------|--------|--------|
| **Puerto Público** | 8002 (HTTP) | Expuesto a red local |
| **Autenticación** | Ninguna | Cualquiera puede enviar solicitudes |
| **TLS/SSL** | No configurado | Datos en texto plano (HTTP) |
| **Red Docker** | Bridge local | Solo accesible desde host |

### Mejoras Propuestas

1. **HTTPS Reverse Proxy**
   - Usar Nginx/Caddy delante de Uvicorn
   - Terminar TLS en proxy
   - Certificados Let's Encrypt

2. **Autenticación**
   - API Key en headers
   - Bearer tokens
   - Validación de origen

3. **Rate Limiting**
   - Limitar solicitudes por IP
   - Prevenir abuso
   - Alertas de anomalías

4. **Firewall Host**
   - iptables para restricción de acceso
   - Solo IPs autorizadas a puerto 8002

---

## Monitoreo y Diagnóstico

### Verificar Conectividad

```bash
# Desde host: ¿Está el puerto escuchando?
netstat -tlnp | grep 8002
ss -tlnp | grep 8002

# Desde host: ¿Responde el servidor?
curl http://localhost:8002/sse

# Desde contenedor: ¿Está activo?
docker ps -a | grep mcp_tools_server
docker logs mcp_tools_server
```

### Verificar Volúmenes

```bash
# Ver volúmenes del contenedor
docker inspect mcp_tools_server | grep -A 10 "Mounts"

# Ver contenido de volumen desde host
ls -la /mnt/disco2/cjhirashi-data/mcp-outputs/
ls -la /mnt/disco2/cjhirashi-data/mcp-outputs/cvs/
ls -la /mnt/disco2/cjhirashi-data/mcp-outputs/cover_letters/

# Acceso desde contenedor
docker exec -it mcp_tools_server ls -la /app/outputs/
docker exec -it mcp_tools_server du -sh /app/outputs/
```

### Monitoreo de Red

```bash
# Ver interfaces de red del contenedor
docker exec mcp_tools_server ip addr show

# Ver conexiones activas del contenedor
docker exec mcp_tools_server netstat -tlnp

# Verificar conectividad a otros servicios
docker exec mcp_tools_server curl http://otra-app:8080
```

---

## Referencias

- [ARCHITECTURE.md](./ARCHITECTURE.md) — Arquitectura del sistema
- [DATA_FLOW.md](./DATA_FLOW.md) — Flujo de datos
- [COLOR_PALETTE.md](../COLOR_PALETTE.md) — Paleta de colores de documentación
- [docker-compose.yml](../docker-compose.yml) — Configuración completa

**Actualizado**: 2026-08-15
