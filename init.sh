#!/bin/bash
set -e

echo "🔍 Ejecutando verificación del arnés..."

# 1. Verificar archivos críticos del arnés
if [ ! -f "AGENTS.md" ]; then
    echo "❌ Error: Falta el archivo AGENTS.md"
    exit 1
fi

if [ ! -d "progress" ]; then
    echo "📁 Creando carpeta de progreso externa..."
    mkdir -p progress
fi

# 2. Validaciones técnicas de tu proyecto (Ejemplo Node.js / Python / Genérico)
# Descomenta o adapta según tu tecnología principal:
# if [ -f "package.json" ]; then
#     npm run test --silent
# fi

echo "✅ ¡Arnés verificado con éxito! El entorno está listo para operar."