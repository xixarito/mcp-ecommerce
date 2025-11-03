#!/bin/bash
# 🚀 Script de inicio rápido para MCP Hybris E-commerce

echo "🛒 Iniciando MCP Hybris E-commerce con ReAct y Reflexión SEO"
echo "=============================================================="

# Verificar si estamos en el directorio correcto
if [ ! -f "server_simple.py" ]; then
    echo "❌ Error: No se encuentra server_simple.py"
    echo "   Asegúrate de ejecutar este script desde el directorio mcp_react"
    exit 1
fi

# Verificar entorno virtual
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Activando entorno virtual..."
    source .venv/bin/activate
    if [ $? -ne 0 ]; then
        echo "❌ Error: No se pudo activar el entorno virtual"
        echo "   Verifica la ruta: .venv"
        exit 1
    fi
else
    echo "✅ Entorno virtual activo: $VIRTUAL_ENV"
fi

# Verificar dependencias
echo "🔍 Verificando dependencias..."
python -c "import flask" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Flask no está instalado. Instalando..."
    pip install flask python-dotenv
fi

echo "✅ Dependencias verificadas"
echo ""
echo "🚀 Iniciando servidor en puerto 5001..."
echo "📱 Demo ReAct: http://localhost:5001/demo"
echo "🔍 Demo SEO: http://localhost:5001/seo-demo"
echo "📊 API Info: http://localhost:5001/"
echo ""
echo "⚡ Presiona Ctrl+C para detener el servidor"
echo "=============================================================="

# Ejecutar servidor
python server_simple.py