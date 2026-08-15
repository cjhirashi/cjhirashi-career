# Topología de Red — MCP Tools Server

_Configuración de red, puertos, volúmenes y conectividad del sistema._

## Diagrama de Topología General

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#06B6D4',
    'primaryTextColor': '#ffffff',
    'primaryBorderColor': '#0891B2',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7',
    'lineColor': '#059669',
    'fontSize': '13px'
  }
}}%%

graph TB
  subgraph external["🌐 Red Externa"]
    CLIENT["Cliente Web<br/>Navegador"]
  end

  subgraph host["🖥️ Host Machine (Linux)"]
    PORT8002["Puerto 8002<br/>(HTTP Listening)"]
    MOUNT["Punto de Montaje<br/>/mnt/disco2/cjhirashi-data/"]
    DIRS["<br/>mcp-outputs/<br/>├── cvs/<br/>└── cover_letters/"]
  end

  subgraph network["🔗 Docker Network"]
    BRIDGE["network-cjhirashi-srv<br/>(Docker Bridge)"]
  end

  subgraph container["🐳 Contenedor Docker"]
    CONT["mcp_tools_server<br/>Python 3.11 + FastMCP"]
    PORT8000["Puerto 8000<br/>(Uvicorn Server)"]
    APPDIR["Directorio App<br/>/app"]
    VOLMOUNT["Volume Mount<br/>/app/outputs"]
  end

  CLIENT -->|"HTTP Request<br/>POST /sse"| PORT8002
  PORT8002 -->|"Port Mapping<br/>8002→8000"| PORT8000
  PORT8000 -->|"Escucha en"| CONT
  CONT -->|"Pertenece a"| BRIDGE
  BRIDGE -->|"Conecta a"| network

  MOUNT <-->|"Bind Volume"| VOLMOUNT
  VOLMOUNT -->|"Escribe PDFs"| DIRS
  VOLMOUNT <-->|"Lectura/Escritura"| CONT

  CONT -->|"Read"| APPDIR

  classDef externalStyle fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff
  classDef hostStyle fill:#f0f9fc,stroke:#059669,stroke-width:2px,color:#333
  classDef networkStyle fill:#10B981,stroke:#059669,stroke-width:2px,color:#fff
  classDef containerStyle fill:#06B6D4,stroke:#0891B2,stroke-width:2px,color:#fff
  classDef portStyle fill:#A855F7,stroke:#9333EA,stroke-width:2px,color:#fff

  class CLIENT externalStyle
  class external externalStyle
  class PORT8002,MOUNT,DIRS hostStyle
  class host hostStyle
  class BRIDGE,network networkStyle
  class CONT,PORT8000,APPDIR,VOLMOUNT containerStyle
  class container containerStyle
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
    'tertiaryColor': '#A855F7'
  }
}}%%

graph LR
  HOST["Host<br/>/mnt/disco2/<br/>cjhirashi-data/<br/>mcp-outputs/"]
  BIND["Bind Volume<br/>(Lectura/Escritura)"]
  CONT["Contenedor<br/>/app/outputs/"]
  
  HOST <-->|"Sincronizado"| BIND
  BIND <-->|"Montado en"| CONT
  
  CONT -->|"Escribe"| PDF["pdf_file.pdf"]
  PDF -->|"Accesible desde"| HOST
  
  style HOST fill:#f0f9fc,stroke:#059669,color:#333
  style BIND fill:#10B981,stroke:#059669,color:#fff
  style CONT fill:#06B6D4,stroke:#0891B2,color:#fff
  style PDF fill:#A855F7,stroke:#9333EA,color:#fff
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
    'primaryColor': '#06B6D4',
    'secondaryColor': '#10B981',
    'tertiaryColor': '#A855F7',
    'lineColor': '#059669'
  }
}}%%

sequenceDiagram
  participant BROWSER as Navegador (Cliente)
  participant HOSTNET as Host Network
  participant DOCKER as Docker Daemon
  participant UVICORN as Uvicorn Server
  participant APP as FastMCP App

  BROWSER->>HOSTNET: TCP SYN → localhost:8002
  HOSTNET->>DOCKER: Port Forward 8002→8000
  DOCKER->>UVICORN: Conexión establecida
  UVICORN->>APP: Nuevo Request
  BROWSER->>UVICORN: HTTP POST /sse<br/>crear_cv_pdf(datos, archivo)
  UVICORN->>APP: Procesa solicitud
  APP->>APP: Genera PDF
  APP->>HOSTNET: Escribe a /mnt/.../mcp-outputs/
  APP->>UVICORN: Respuesta SSE
  UVICORN->>BROWSER: SSE Event: "PDF Generado"
  BROWSER->>HOSTNET: GET /download/archivo.pdf
  HOSTNET->>HOSTNET: Lee archivo de volumen
  HOSTNET->>BROWSER: PDF File (descarga)
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
