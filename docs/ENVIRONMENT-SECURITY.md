# Estrategia de Seguridad: Variables de Entorno

## 🎯 Resumen Ejecutivo

Este documento define la **mejor práctica de la industria** para manejar variables de entorno en este proyecto. La estrategia es:

```
✅ docker-compose.yml           → EN GIT (sin secretos hardcodeados)
✅ .env.local                   → NO EN GIT (privado, contiene secretos dev)
✅ .env.example                 → EN GIT (plantilla pública, sin valores reales)
✅ .gitignore                   → Bloquea .env.* (excepto .env.example)
✅ CI/CD (GitHub Secrets)       → Variables en Actions secrets para producción
```

---

## 📋 Capas de Configuración

### **Capa 1: Desarrollo Local (env_file)**

**Archivo**: `.env.local` (privado, en `.gitignore`)

**Propósito**: Variables de desarrollo local

```bash
# Contiene valores REALES (cambiar por los tuyos):
POSTGRES_USER=mcpuser
POSTGRES_PASSWORD=mcppass123-dev-only
SECRET_KEY=portafolio-cjhirashi-dev-secret-key-32chars-minimum
DATABASE_URL=postgresql+asyncpg://mcpuser:mcppass123-dev-only@postgres:5432/portafolio_db
```

**Cómo se carga**:
```bash
# docker-compose.yml usa:
env_file: .env.local

# Docker Compose carga automáticamente .env.local en:
# - api_rest
# - postgres
```

---

### **Capa 2: docker-compose.yml (infraestructura)**

**Archivo**: `docker-compose.yml` (versionado en git)

**Propósito**: Define la estructura de servicios (sin secretos hardcodeados)

```yaml
# ✅ CORRECTO: Referencias a variables
services:
  postgres:
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}

# ❌ NUNCA: Valores hardcodeados
# environment:
#   POSTGRES_PASSWORD: "mcppass123"  # ¡EXPONE SECRETO!
```

**Por qué es seguro**:
- El compose describe *qué* variables necesita (no *qué valores* son)
- Cualquier dev puede ver la estructura sin ver los secretos
- Los valores reales vienen de `.env.local` (ignorado en git)

---

### **Capa 3: Plantilla Pública (.env.example)**

**Archivo**: `.env.example` (versionado en git)

**Propósito**: Template para nuevos devs / CI/CD

```bash
# Placeholder: SIN valores reales
POSTGRES_USER=mcpuser
POSTGRES_PASSWORD=your-secure-password-here-min-20-chars
SECRET_KEY=your-secret-key-min-32-chars-change-in-production
```

**Cómo usarlo**:
```bash
# Nuevo dev:
cp .env.example .env.local
nano .env.local  # Llenar con valores reales

# El archivo es autodescriptivo:
# - Qué variables se necesitan
# - Formato esperado
# - Constraints (min 20 chars, etc)
```

---

### **Capa 4: Producción (GitHub Secrets)**

**Ubicación**: GitHub → Settings → Secrets → Actions Secrets

**Propósito**: Variables para CI/CD y deployments a producción

```bash
# Variables guardadas en GitHub (no en repo):
DATABASE_URL_PROD
SECRET_KEY_PROD
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
```

**Cómo se usan en CI/CD**:
```yaml
# .github/workflows/deploy.yml
env:
  DATABASE_URL: ${{ secrets.DATABASE_URL_PROD }}
  SECRET_KEY: ${{ secrets.SECRET_KEY_PROD }}
```

---

## 🛡️ Seguridad: Cómo Evitar Exponer Secretos

### **1. Verificar que `.env.local` está ignorado**

```bash
# Ver si git está trackeando .env.local
git status
git ls-files | grep ".env"

# Debería estar vacío. Si ves .env.local, arreglar:
git rm --cached .env.local  # Remove from tracking
git commit -m "Remove .env.local from version control"
```

### **2. Verificar .gitignore está correcto**

```bash
# Ver reglas de .gitignore
cat .gitignore | grep -A 5 "Environment"

# Debe contener:
.env
.env.local
.env.*.local
!.env.example  # Permitir que .env.example esté en git
```

### **3. Nunca hacer:**

```bash
❌ git add .env.local                          # Never
❌ docker-compose.yml con secretos              # Never
❌ Commitar AWS keys, DB passwords, API keys   # Never
❌ Push a GitHub sin revisar git status        # Never
```

### **4. Si accidentalmente commiteaste un secreto:**

```bash
# ⚠️ EMERGENCIA: Un secreto está en git

# Opción 1: Remover del historio (mejor)
git filter-branch --tree-filter 'rm -f .env.local' HEAD

# Opción 2: Simplemente cambiar el secreto (más fácil)
# 1. Cambiar contraseña en la BD
# 2. Cambiar SECRET_KEY en aplicación
# 3. Cambiar AWS keys en IAM
# 4. Invalidar tokens viejos

# Luego, subir fix commit
git add -A
git commit -m "Remove accidental secrets from history"
git push origin main
```

---

## 📝 Checklist de Setup Seguro

Cuando levantes el sistema por primera vez:

```
☐ Copiar .env.example → .env.local
☐ Cambiar todas las contraseñas en .env.local
  ☐ POSTGRES_PASSWORD: 20+ caracteres aleatorios
  ☐ SECRET_KEY: 32+ caracteres aleatorios (use `openssl rand -hex 16`)
  ☐ BEDROCK_REGION/MODEL_ID: agregar si usas AWS Bedrock
  ☐ ADZUNA_APP_ID / ADZUNA_APP_KEY: requeridas para buscar Indeed
☐ Verificar .gitignore contiene .env.local
☐ Verificar git status NO muestra .env.local
☐ docker compose --env-file .env.local up -d
☐ Probar que servicios están saludables: docker compose ps
☐ NO compartir .env.local en Slack, email, etc.
```

---

## 🔄 Flujo: Desarrollo Local vs Producción

### **Desarrollo Local**

```
.env.example
    ↓
cp → .env.local (privado, no versionado)
    ↓
docker-compose.yml (env_file: .env.local)
    ↓
docker compose up -d
    ↓
http://localhost:8003
```

### **Producción (via GitHub)**

```
GitHub Secrets (DATABASE_URL_PROD, SECRET_KEY_PROD, etc.)
    ↓
.github/workflows/deploy.yml (env: ${{ secrets.XXX }})
    ↓
docker-compose.yml (env_file: .env) # En producción, .env es inyectado por orquestador
    ↓
Deploy a VPS / Kubernetes
    ↓
https://portafolio.cjhirashi.com
```

---

## 🎓 Referencias

- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [Docker Compose: env_file](https://docs.docker.com/compose/compose-file/compose-file-v3/#env_file)
- [GitHub Actions: Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [12-Factor App: Store config in environment](https://12factor.net/config)

---

**Última Actualización**: 2026-08-17  
**Responsable**: Code Quality Guardian (Seguridad)  
**Estado**: ✅ Implementado y verificado
