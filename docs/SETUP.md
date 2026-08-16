# 🔒 Guía de Configuración - Portafolio-cjhirashi

## ⚠️ SEGURIDAD CRÍTICA

Este repositorio es **PÚBLICO en GitHub**. Nunca commitees archivos `.env` o información sensible.

---

## 🚀 Primer Setup

### 1. Crear archivo `.env.local`

```bash
cp .env.example .env.local
```

### 2. Editar `.env.local` con valores reales

```bash
# Abre .env.local y reemplaza todos los valores:
nano .env.local
```

**Variables críticas a cambiar:**

| Variable | Cambiar | Ejemplo |
|----------|---------|---------|
| `POSTGRES_PASSWORD` | ✅ SI | `super-secure-password-32-chars-min` |
| `SECRET_KEY` | ✅ SI | `your-app-secret-key-min-32-chars` |
| `BEDROCK_REGION` | ✅ SI | `us-east-1` (tu región AWS) |
| `BEDROCK_MODEL_ID` | ✅ SI | `anthropic.claude-3-sonnet-20240229-v1:0` |
| `DEBUG` | ⚠️ DEV ONLY | `false` en producción |

### 3. Verificar `.gitignore`

```bash
# Verificar que .env.local está ignorado
git status | grep .env
# NO debe aparecer .env.local
```

---

## 🐳 Ejecutar Docker Compose

```bash
docker compose up -d
```

Docker cargará automáticamente `.env.local` para todas las variables.

---

## 🔐 Checklist de Seguridad

Antes de hacer commit o push:

```
☐ .env.local NUNCA está en git (check: git status)
☐ .env.example tiene placeholders, NO valores reales
☐ .gitignore incluye .env, .env.local, .env.*.local
☐ SECRET_KEY es una string aleatoria >= 32 caracteres
☐ POSTGRES_PASSWORD es >= 20 caracteres
☐ DEBUG=false en producción
☐ AWS credentials (si se usan) están en variables, NO hardcodeadas
```

---

## 📝 Notas de Desarrollo

### Archivos `.env` en el proyecto:

| Archivo | Versiona | Propósito |
|---------|----------|-----------|
| `.env.example` | ✅ SÍ | Template público con placeholders |
| `.env.local` | ❌ NO | Configuración local con valores reales |
| `.env.prod` | ❌ NO | (Si aplica) Configuración de producción |

### Para agregar nueva variable:

1. Agregar a `.env.example` con placeholder
2. Agregar a `.env.local` con valor real
3. Usar en `docker-compose.yml` como `${VARIABLE_NAME}`

---

## 🆘 Troubleshooting

### ".env not found" error:

```bash
# Verificar que .env.local existe en la raíz
ls -la .env.local
# Si no existe, copiar desde example
cp .env.example .env.local
```

### Variables no se cargan en Docker:

```bash
# Verificar que env_file está en docker-compose.yml
grep -A 2 "env_file:" docker-compose.yml
# Debe mostrar: env_file: .env.local

# Reiniciar compose
docker compose down
docker compose up -d
```

### PostgreSQL connection error:

```bash
# Verificar que los valores en .env.local son válidos
grep POSTGRES .env.local
# Coincidir con DATABASE_URL

# Ver logs
docker compose logs postgres
```

---

## 🚨 Si accidentalmente commiteaste información sensible:

```bash
# STOP. No hables. Notifica al equipo.
# Reverte el commit:
git reset --soft HEAD~1
git reset HEAD .env
git commit -m "Remove .env from commit"

# Genera nuevas credenciales en todos los sistemas
```

---

**Last Updated:** 2026-08-16  
**Responsable:** Portafolio-cjhirashi Security Team
