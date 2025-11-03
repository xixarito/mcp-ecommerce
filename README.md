# NextGen Dev AI - MCP con ReAct & Reflexion

Sistema MCP (Model Context Protocol) optimizado que implementa los patrones ReAct y Reflexion para consulta de productos de e-commerce Hybris y mejora automática de descripciones SEO.

## 🚀 Características

- **Patrón ReAct**: Think → Act → Observe para consultas de productos
- **Patrón Reflexion**: Actor → Evaluator → Reflector para mejora de descripciones SEO
- **Integración con LLM**: Utiliza ChatOpenAI para generación inteligente de contenido
- **API REST**: Interfaz web completa para interacción
- **Optimización SEO**: Mejora automática de descripciones de productos

## 📁 Estructura del Proyecto (Optimizada)

```
mcp-ecommerce/
├── .env                    # Variables de entorno (OPENAI_API_KEY)
├── requirements.txt        # Dependencias Python
├── README.md              # Documentación
└── mcp_react/            # Aplicación principal
    ├── server_simple.py   # Servidor optimizado (910 líneas)
    ├── react/            # Implementación patrón ReAct
    ├── reflexion/        # Implementación patrón Reflexion
    ├── models/           # Modelos de datos
    ├── static/           # Archivos estáticos web
    └── templates/        # Templates HTML
```

## ⚡ Inicio Rápido

1. **Navegar a la aplicación:**
```bash
cd mcp-ecommerce/mcp_react
```

2. **Ejecutar el servidor:**
```bash
python server_simple.py
```

3. **Abrir las interfaces web:**
   - Demo ReAct: http://localhost:5001/demo
   - SEO Reflexion: http://localhost:5001/seo
   - Health Check: http://localhost:5001/health

## 🔧 Configuración

Asegúrate de tener tu API key de OpenAI en el archivo `.env`:
```env
OPENAI_API_KEY=tu_api_key_aqui
```

## 🎯 Patrones Implementados

### Patrón ReAct para E-commerce
El sistema implementa el ciclo ReAct aplicado a consultas de productos:
1. **Think** (Pensar): Analiza la consulta del usuario sobre productos
2. **Act** (Actuar): Ejecuta herramientas de e-commerce (búsqueda, detalles, stock)
3. **Observe** (Observar): Procesa resultados de las herramientas
4. **Repetir**: Continúa hasta obtener respuesta completa

### Patrón Reflexion para SEO
Mejora automática de descripciones de productos:
1. **Actor**: Genera descripción inicial
2. **Evaluator**: Evalúa calidad SEO y legibilidad
3. **Reflector**: Mejora basándose en evaluación

## 🛠️ Herramientas Disponibles

### ReAct Tools
- `search_products[término]`: Busca productos en el catálogo
- `get_product_details[id]`: Obtiene detalles de un producto específico
- `check_stock[id]`: Verifica disponibilidad
- `get_price_history[id]`: Historial de precios
- `finish[respuesta]`: Proporciona respuesta final

### Reflexion Tools
- `improve_seo_description`: Mejora automática de descripciones
- `evaluate_content`: Evaluación de calidad de contenido
- `generate_keywords`: Generación de palabras clave SEO

## 🔍 Estado del Proyecto

✅ **Completado:**
- Implementación dual de patrones ReAct y Reflexion
- Integración completa con ChatOpenAI
- Servidor optimizado (910 líneas)
- Interfaces web funcionales
- Limpieza y optimización de código

🎯 **Funcionalidad Principal:**
- Servidor en `mcp_react/server_simple.py`
- Ambos patrones funcionando con LLM real
- APIs REST completamente funcionales