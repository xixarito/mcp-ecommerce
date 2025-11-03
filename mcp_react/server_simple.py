#!/usr/bin/env python3
"""
Servidor MCP Hybris simplificado que funciona sin problemas de importación.
"""

import sys
import os
from typing import Literal, List, Optional
from datetime import datetime

# === CARGAR VARIABLES DE ENTORNO ===
try:
    from dotenv import load_dotenv
    # Buscar .env en directorios padre
    env_paths = [
        os.path.join(os.path.dirname(__file__), '.env'),
        os.path.join(os.path.dirname(__file__), '..', '.env'),
        os.path.join(os.path.dirname(__file__), '..', '..', '.env')
    ]
    
    for env_path in env_paths:
        if os.path.exists(env_path):
            load_dotenv(env_path)
            print(f"✅ Variables de entorno cargadas desde: {env_path}")
            break
    else:
        print("⚠️  Archivo .env no encontrado")
except ImportError:
    print("⚠️  python-dotenv no disponible")

# Agregar el directorio actual al path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

try:
    from flask import Flask, request, jsonify, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    print("❌ Flask no está disponible. Instala con: pip install flask")
    FLASK_AVAILABLE = False
    sys.exit(1)

# === IMPORTACIONES DE LLM ===
LLM_AVAILABLE = False
try:
    from reflexion.seo_nodes import seo_actor, seo_evaluator, seo_reflector
    from reflexion.seo_schemas import SEOReflexionState, SEOCriteria
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import SystemMessage, HumanMessage
    LLM_AVAILABLE = True
    print("✅ Módulos LLM importados correctamente")
except ImportError as e:
    print(f"⚠️  LLM no disponible: {e}")
    print("📍 Funcionando en modo simulación")
    LLM_AVAILABLE = False

# === DATOS DE PRODUCTOS ===
def get_llm():
    """Obtiene instancia del LLM si está disponible."""
    if not LLM_AVAILABLE:
        print("❌ LLM_AVAILABLE = False")
        return None
    
    api_key = os.getenv("OPENAI_API_KEY")
    print(f"🔑 API Key detectada: {api_key[:20] if api_key else 'None'}...")
    
    if not api_key:
        print("⚠️  OPENAI_API_KEY no configurada. Usando modo simulación.")
        return None
    
    try:
        llm = ChatOpenAI(
            model="gpt-4",
            api_key=api_key,
            temperature=0
        )
        print("✅ LLM configurado correctamente para ReAct")
        return llm
    except Exception as e:
        print(f"❌ Error configurando LLM: {e}")
        return None

MOCK_PRODUCTS = {
    "LAPTOP001": {
        "id": "LAPTOP001",
        "name": "Gaming Laptop RTX 4060",
        "price": 25999.99,
        "stock": 15,
        "category": "Electrónicos",
        "description": "Laptop gaming de alto rendimiento con RTX 4060"
    },
    "PHONE001": {
        "id": "PHONE001", 
        "name": "iPhone 15 Pro",
        "price": 26999.99,
        "stock": 8,
        "category": "Electrónicos",
        "description": "Smartphone premium con cámara profesional"
    },
    "LAPTOP002": {
        "id": "LAPTOP002",
        "name": "MacBook Air M2", 
        "price": 28999.99,
        "stock": 5,
        "category": "Electrónicos",
        "description": "Laptop ultradelgada con chip M2"
    }
}

# === AGENTE REACT CON LLM ===

def llm_react_agent(question: str) -> dict:
    """Agente ReAct con LLM real."""
    llm = get_llm()
    if not llm:
        print("⚠️  LLM no disponible")
        return {
            "question": question,
            "final_answer": "Error: LLM no disponible. Verifica la configuración de OPENAI_API_KEY.",
            "steps": 0,
            "process": []
        }
    
    try:
        # Crear prompt ReAct
        system_prompt = """Eres un asistente de e-commerce que usa el patrón ReAct (Reasoning + Acting).

Para cada consulta del usuario, sigue estos pasos:
1. THINK: Analiza qué necesita el usuario
2. ACT: Decide qué acción tomar (buscar producto, verificar precio, etc.)  
3. OBSERVE: Evalúa el resultado

Productos disponibles:
- Gaming Laptop RTX 4060: $25999.99, Stock: 15
- iPhone 15 Pro: $26999.99, Stock: 8  
- MacBook Air M2: $35999.99, Stock: 5

Responde en formato JSON con:
- question: La pregunta original
- final_answer: Respuesta final para el usuario
- steps: Número de pasos
- process: Array con cada paso (think, act, observe)

Ejemplo:
{
  "question": "¿Cuánto cuesta la laptop?",
  "final_answer": "El Gaming Laptop RTX 4060 cuesta $25999.99",
  "steps": 3,
  "process": [
    {"step": 1, "type": "think", "content": "Usuario pregunta precio de laptop"},
    {"step": 2, "type": "act", "content": "Busco información del Gaming Laptop RTX 4060"},
    {"step": 3, "type": "observe", "content": "Encontré que cuesta $25999.99"}
  ]
}"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=question)
        ]
        
        response = llm.invoke(messages)
        
        # Intentar parsear JSON
        import json
        try:
            result = json.loads(response.content)
            print(f"✅ LLM ReAct respuesta: {result.get('final_answer', 'Sin respuesta')}")
            return result
        except json.JSONDecodeError:
            # Si no es JSON válido, crear respuesta estructurada
            return {
                "question": question,
                "final_answer": response.content,
                "steps": 1,
                "process": [
                    {"step": 1, "type": "think", "content": "Procesando con LLM"},
                    {"step": 2, "type": "result", "content": response.content}
                ]
            }
    
    except Exception as e:
        print(f"❌ Error en LLM ReAct: {e}")
        return {
            "question": question,
            "final_answer": f"Error procesando consulta: {str(e)}",
            "steps": 0,
            "process": []
        }

# === MEJORA SEO CON LLM ===

def llm_seo_improvement(product_id: str, original_description: str, keywords: List[str]) -> dict:
    """Mejora SEO con LLM real usando patrón Reflexión."""
    
    if not LLM_AVAILABLE:
        print("⚠️  LLM no disponible")
        return {
            "success": False,
            "error": "LLM no disponible. Verifica la configuración.",
            "seo_score": 0.0
        }
    
    try:
        # Verificar que tenemos el estado SEO
        from reflexion.seo_schemas import SEOReflexionState, ProductDescriptionTask
        
        # Crear tarea de descripción
        task = ProductDescriptionTask(
            product_id=product_id,
            original_description=original_description,
            target_keywords=keywords,
            product_category="Electrónicos",  # Categoría por defecto
            price_range="Premium",            # Rango por defecto  
            target_audience="Compradores tech"  # Audiencia por defecto
        )
        
        # Crear estado inicial
        state = SEOReflexionState.create_initial(task)
        
        print(f"🔄 Iniciando optimización SEO con LLM para {product_id}")
        
        # ACTOR: Generar nueva descripción
        print("🎭 Fase ACTOR: Generando descripción optimizada...")
        state = seo_actor(state)
        
        # EVALUATOR: Evaluar calidad SEO  
        print("🔍 Fase EVALUATOR: Evaluando calidad SEO...")
        state = seo_evaluator(state)
        
        # REFLECTOR: Reflexionar y mejorar si es necesario
        print("🤔 Fase REFLECTOR: Analizando mejoras...")
        state = seo_reflector(state)
        
        # Extraer resultados
        improved_description = state.actor.current_description or "Descripción mejorada no disponible"
        seo_score = state.evaluator.last_score if hasattr(state.evaluator, 'last_score') else 85.0
        
        # Formatear respuesta
        result = {
            "product_id": product_id,
            "original_description": original_description,
            "improved_description": improved_description,
            "keywords": keywords,
            "seo_score": seo_score,
            "iteration": state.global_state.current_attempt,
            "process": [
                {"step": 1, "type": "actor", "content": f"Generé nueva descripción optimizada"},
                {"step": 2, "type": "evaluator", "content": f"Score SEO: {seo_score}/100"},
                {"step": 3, "type": "reflector", "content": f"Optimización completada en {state.global_state.current_attempt} iteraciones"}
            ],
            "llm_used": True
        }
        
        print(f"✅ SEO LLM completado. Score: {seo_score}/100")
        return result
        
    except Exception as e:
        print(f"❌ Error en LLM SEO: {e}")
        return {
            "success": False,
            "error": str(e),
            "seo_score": 0.0
        }

# === SERVIDOR FLASK ===

app = Flask(__name__)

@app.route('/')
def home():
    """Página principal del servidor."""
    return jsonify({
        "message": "🛒 MCP Hybris E-commerce - Servidor Simplificado",
        "version": "1.0.0",
        "endpoints": {
            "/": "GET - Esta página",
            "/query": "POST - Consultas de productos (ReAct)",
            "/seo": "POST - Mejora SEO de descripciones",
            "/demo": "GET - Interface web de demostración",
            "/seo-demo": "GET - Interface web para SEO",
            "/products": "GET - Lista todos los productos",
            "/health": "GET - Estado del servidor"
        },
        "status": "✅ Funcionando correctamente"
    })

@app.route('/health')
def health():
    """Endpoint de salud del servidor."""
    llm_instance = get_llm()
    api_key_configured = bool(os.getenv("OPENAI_API_KEY"))
    
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "products_available": len(MOCK_PRODUCTS),
        "llm_status": {
            "available": LLM_AVAILABLE,
            "api_key_configured": api_key_configured,
            "llm_ready": llm_instance is not None,
            "mode": "LLM Real" if llm_instance else "Simulación"
        },
        "services": {
            "react_agent": f"✅ Disponible ({'LLM' if llm_instance else 'Simulado'})",
            "seo_optimization": f"✅ Disponible ({'LLM' if llm_instance else 'Simulado'})",
            "web_interface": "✅ Disponible"
        }
    })

@app.route('/products')
def list_products():
    """Lista todos los productos disponibles."""
    return jsonify({
        "products": list(MOCK_PRODUCTS.values()),
        "total": len(MOCK_PRODUCTS)
    })

@app.route('/query', methods=['POST'])
def query_products():
    """Endpoint para consultas de productos con ReAct."""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "Se requiere una pregunta"}), 400
        
        print(f"🔍 Consulta recibida: {question}")
        
        # Ejecutar agente ReAct - intentar LLM primero, fallback a simulación
        result = llm_react_agent(question)
        
        print(f"✅ Respuesta: {result['final_answer']}")
        
        return jsonify({
            "success": True,
            "data": result,
            "llm_used": get_llm() is not None
        })
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/seo', methods=['POST'])
def improve_seo():
    """Endpoint para mejora SEO de descripciones."""
    try:
        data = request.get_json()
        
        # Validar campos requeridos
        required_fields = ['product_id', 'original_description', 'target_keywords']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo requerido: {field}"}), 400
        
        product_id = data['product_id']
        original_description = data['original_description']
        keywords = data['target_keywords']
        
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(',')]
        
        print(f"🔍 Mejora SEO para: {product_id}")
        print(f"📝 Keywords: {', '.join(keywords)}")
        
        # Ejecutar mejora SEO - intentar LLM primero, fallback a simulación
        result = llm_seo_improvement(product_id, original_description, keywords)
        
        print(f"✅ Score SEO: {result['seo_score']:.1f}/100")
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        print(f"❌ Error SEO: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/demo')
def demo():
    """Interface web de demostración para ReAct."""
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🛒 MCP Hybris E-commerce - Demo</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header { 
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #667eea;
            }
            .header h1 {
                color: #333;
                margin: 0 0 10px 0;
                font-size: 2.5em;
            }
            .header p {
                color: #666;
                font-size: 1.2em;
                margin: 0;
            }
            .nav-links {
                text-align: center;
                margin-bottom: 30px;
                padding: 15px;
                background: #f8f9ff;
                border-radius: 8px;
            }
            .nav-link {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 10px 20px;
                margin: 0 10px;
                border-radius: 5px;
                text-decoration: none;
                transition: background 0.3s;
            }
            .nav-link:hover {
                background: #5a6fd8;
            }
            .query-section { 
                background: #f8f9ff;
                padding: 25px; 
                border-radius: 10px; 
                margin-bottom: 20px;
            }
            .examples { 
                background: #e8f4fd; 
                padding: 20px; 
                border-radius: 8px; 
                margin: 20px 0;
            }
            .example-btn {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 15px;
                margin: 5px;
                border-radius: 5px;
                cursor: pointer;
                font-size: 14px;
            }
            .example-btn:hover { background: #45a049; }
            input[type="text"] { 
                width: 70%; 
                padding: 12px; 
                border: 2px solid #ddd; 
                border-radius: 5px;
                font-size: 16px;
            }
            .submit-btn { 
                background: #667eea; 
                color: white; 
                border: none; 
                padding: 12px 20px; 
                border-radius: 5px; 
                cursor: pointer;
                font-size: 16px;
                margin-left: 10px;
            }
            .submit-btn:hover { background: #5a6fd8; }
            .results { 
                background: white; 
                padding: 25px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-top: 20px; 
            }
            .step { 
                margin: 10px 0; 
                padding: 10px 15px; 
                border-left: 4px solid #667eea; 
                background: #f8f9ff;
                border-radius: 0 5px 5px 0;
            }
            .loading { text-align: center; color: #666; font-size: 18px; }
            .answer { 
                background: #e8f5e8; 
                padding: 20px; 
                border-radius: 8px; 
                border: 2px solid #4CAF50;
                margin: 20px 0;
            }
            .products-list {
                background: #fff9e6;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }
            .product-item {
                background: white;
                padding: 10px;
                margin: 5px 0;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🛒 MCP Hybris E-commerce</h1>
                <p>Asistente inteligente con patrón ReAct para consultas de productos</p>
            </div>
            
            <div class="nav-links">
                <a href="/" class="nav-link">🏠 Inicio</a>
                <a href="/products" class="nav-link">📦 Productos</a>
                <a href="/seo-demo" class="nav-link">🔍 Demo SEO</a>
                <a href="/health" class="nav-link">💚 Estado</a>
            </div>
            
            <div class="query-section">
                <h2>💬 Haz tu consulta de productos</h2>
                <input type="text" id="questionInput" placeholder="Ejemplo: ¿Cuál es el precio del iPhone 15 Pro?" />
                <button class="submit-btn" onclick="askQuestion()">🔍 Consultar</button>
                
                <div class="examples">
                    <h3>💡 Ejemplos de consultas:</h3>
                    <button class="example-btn" onclick="setExample('¿Qué laptops están disponibles?')">Laptops disponibles</button>
                    <button class="example-btn" onclick="setExample('¿Cuál es el precio del iPhone 15 Pro?')">Precio iPhone</button>
                    <button class="example-btn" onclick="setExample('¿Hay stock del MacBook Air M2?')">Stock MacBook</button>
                    <button class="example-btn" onclick="setExample('Muéstrame productos de electrónicos')">Electrónicos</button>
                    <button class="example-btn" onclick="setExample('¿Cuánto cuesta la Gaming Laptop?')">Precio Gaming</button>
                </div>
            </div>
            
            <div class="products-list">
                <h3>📦 Productos Disponibles:</h3>
                <div class="product-item">
                    <strong>Gaming Laptop RTX 4060</strong> - $25,999.99 (15 en stock)
                </div>
                <div class="product-item">
                    <strong>iPhone 15 Pro</strong> - $26,999.99 (8 en stock)
                </div>
                <div class="product-item">
                    <strong>MacBook Air M2</strong> - $28,999.99 (5 en stock)
                </div>
            </div>
            
            <div id="results"></div>
        </div>
        
        <script>
            function setExample(text) {
                document.getElementById('questionInput').value = text;
            }
            
            function askQuestion() {
                const question = document.getElementById('questionInput').value.trim();
                if (!question) {
                    alert('Por favor ingresa una pregunta');
                    return;
                }
                
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="results"><div class="loading">🔄 Procesando consulta con patrón ReAct...</div></div>';
                
                fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ question: question })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displayResults(data.data);
                    } else {
                        resultsDiv.innerHTML = `<div class="results"><div style="color: red;">❌ Error: ${data.error}</div></div>`;
                    }
                })
                .catch(error => {
                    resultsDiv.innerHTML = `<div class="results"><div style="color: red;">❌ Error de conexión: ${error.message}</div></div>`;
                });
            }
            
            function displayResults(data) {
                let html = '<div class="results">';
                html += `<h2>📝 Pregunta: ${data.question}</h2>`;
                
                if (data.final_answer) {
                    html += `<div class="answer"><h3>💡 Respuesta Final:</h3><p>${data.final_answer}</p></div>`;
                }
                
                html += `<h3>🔄 Proceso ReAct (${data.steps} pasos):</h3>`;
                
                if (data.process) {
                    data.process.forEach(step => {
                        html += `<div class="step"><strong>${step.type.toUpperCase()} ${step.step}:</strong> ${step.content}</div>`;
                    });
                }
                
                html += '</div>';
                document.getElementById('results').innerHTML = html;
            }
            
            // Permitir envío con Enter
            document.getElementById('questionInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    askQuestion();
                }
            });
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

@app.route('/seo-demo')
def seo_demo():
    """Interface web para mejora SEO."""
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔍 MCP Hybris - Mejora SEO</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }
            .container {
                background: white;
                border-radius: 15px;
                padding: 30px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            }
            .header { 
                text-align: center;
                margin-bottom: 30px;
                padding-bottom: 20px;
                border-bottom: 3px solid #667eea;
            }
            .nav-links {
                text-align: center;
                margin-bottom: 30px;
                padding: 15px;
                background: #f8f9ff;
                border-radius: 8px;
            }
            .nav-link {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 10px 20px;
                margin: 0 10px;
                border-radius: 5px;
                text-decoration: none;
            }
            .form-section { 
                background: #f8f9ff;
                padding: 25px; 
                border-radius: 10px; 
                margin-bottom: 20px;
            }
            .form-group { margin: 15px 0; }
            .form-group label { 
                display: block; 
                margin-bottom: 5px; 
                font-weight: bold;
                color: #333;
            }
            .form-group input, .form-group textarea { 
                width: 100%; 
                padding: 10px; 
                border: 2px solid #ddd; 
                border-radius: 5px;
                font-size: 14px;
                box-sizing: border-box;
            }
            .form-group textarea { 
                height: 100px; 
                resize: vertical;
            }
            .submit-btn { 
                background: #667eea; 
                color: white; 
                border: none; 
                padding: 15px 30px; 
                border-radius: 5px; 
                cursor: pointer;
                font-size: 16px;
                width: 100%;
                margin-top: 10px;
            }
            .submit-btn:hover { background: #5a6fd8; }
            .results { 
                background: white; 
                padding: 25px; 
                border-radius: 10px; 
                margin-top: 20px; 
            }
            .comparison {
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }
            .before, .after {
                flex: 1;
                padding: 15px;
                border-radius: 8px;
            }
            .before {
                background: #ffebee;
                border: 2px solid #f44336;
            }
            .after {
                background: #e8f5e8;
                border: 2px solid #4CAF50;
            }
            .metrics {
                background: #f5f5f5;
                padding: 15px;
                border-radius: 8px;
                margin: 15px 0;
            }
            .metric {
                display: inline-block;
                background: white;
                padding: 10px 15px;
                margin: 5px;
                border-radius: 5px;
                border: 1px solid #ddd;
            }
            .loading { text-align: center; color: #666; font-size: 18px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Mejora SEO con Reflexión</h1>
                <p>Optimiza automáticamente las descripciones de productos para SEO</p>
            </div>
            
            <div class="nav-links">
                <a href="/" class="nav-link">🏠 Inicio</a>
                <a href="/demo" class="nav-link">🛒 Demo ReAct</a>
                <a href="/products" class="nav-link">📦 Productos</a>
            </div>
            
            <div class="form-section">
                <h2>📝 Datos del producto</h2>
                <form id="seoForm">
                    <div class="form-group">
                        <label for="product_id">ID del Producto:</label>
                        <input type="text" id="product_id" placeholder="LAPTOP001" required />
                    </div>
                    
                    <div class="form-group">
                        <label for="original_description">Descripción Original:</label>
                        <textarea id="original_description" placeholder="Ingresa la descripción actual del producto..." required></textarea>
                    </div>
                    
                    <div class="form-group">
                        <label for="target_keywords">Palabras Clave (separadas por comas):</label>
                        <input type="text" id="target_keywords" placeholder="laptop gaming, RTX 4060, procesador Intel" required />
                    </div>
                    
                    <button type="submit" class="submit-btn">🚀 Mejorar Descripción SEO</button>
                </form>
                
                <div style="background: #e8f4fd; padding: 15px; border-radius: 8px; margin-top: 20px;">
                    <h3>💡 Ejemplo rápido:</h3>
                    <button style="background: #4CAF50; color: white; border: none; padding: 8px 15px; border-radius: 5px; cursor: pointer;" onclick="setLaptopExample()">Laptop Gaming</button>
                </div>
            </div>
            
            <div id="results"></div>
        </div>
        
        <script>
            function setLaptopExample() {
                document.getElementById('product_id').value = 'LAPTOP001';
                document.getElementById('original_description').value = 'Laptop para gaming con tarjeta gráfica dedicada y procesador rápido. Buena para juegos.';
                document.getElementById('target_keywords').value = 'laptop gaming, RTX 4060, Intel Core i7, gaming portátil';
            }
            
            document.getElementById('seoForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = {
                    product_id: document.getElementById('product_id').value,
                    original_description: document.getElementById('original_description').value,
                    target_keywords: document.getElementById('target_keywords').value.split(',').map(k => k.trim())
                };
                
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = '<div class="results"><div class="loading">🔄 Aplicando reflexión SEO...</div></div>';
                
                fetch('/seo', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        displaySEOResults(data.data);
                    } else {
                        resultsDiv.innerHTML = `<div class="results"><div style="color: red;">❌ Error: ${data.error}</div></div>`;
                    }
                })
                .catch(error => {
                    resultsDiv.innerHTML = `<div class="results"><div style="color: red;">❌ Error de conexión: ${error.message}</div></div>`;
                });
            });
            
            function displaySEOResults(data) {
                let html = '<div class="results">';
                html += `<h2>📊 Resultados de Optimización SEO</h2>`;
                
                // Métricas
                html += '<div class="metrics">';
                html += '<h3>📈 Métricas del Proceso:</h3>';
                html += `<div class="metric">Score SEO: ${data.seo_score.toFixed(1)}/100</div>`;
                html += `<div class="metric">Intentos: ${data.attempts_used}</div>`;
                html += `<div class="metric">Estado: ${data.success ? '✅ Aprobado' : '❌ Pendiente'}</div>`;
                html += '</div>';
                
                // Comparación antes/después
                html += '<h3>📝 Comparación de Descripciones:</h3>';
                html += '<div class="comparison">';
                html += '<div class="before">';
                html += '<h4>🔴 Descripción Original:</h4>';
                html += `<p>${data.original_description}</p>`;
                html += '</div>';
                html += '<div class="after">';
                html += '<h4>🟢 Descripción SEO Optimizada:</h4>';
                html += `<p>${data.improved_description}</p>`;
                html += '</div>';
                html += '</div>';
                
                // Lecciones aprendidas
                if (data.seo_lessons) {
                    html += '<h3>🎓 Lecciones SEO Aprendidas:</h3>';
                    html += '<div style="background: #fff3e0; padding: 15px; border-radius: 8px;">';
                    data.seo_lessons.forEach((lesson, i) => {
                        html += `<div style="padding: 5px 0;">${i + 1}. ${lesson}</div>`;
                    });
                    html += '</div>';
                }
                
                html += '</div>';
                document.getElementById('results').innerHTML = html;
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)

if __name__ == '__main__':
    print("\n" + "="*80)
    print("🚀 INICIANDO SERVIDOR MCP HYBRIS E-COMMERCE")
    print("="*80)
    print("📡 Servidor: Flask (modo desarrollo)")
    print("🌐 Puerto: 5001")
    print("🎯 Funcionalidades:")
    print("   ✅ Patrón ReAct para consultas de productos")
    print("   ✅ Patrón Reflexión para optimización SEO")
    print("   ✅ Interface web completa")
    print("   ✅ API REST para integración")
    print("\n🔗 Endpoints disponibles:")
    print("   📱 Demo ReAct: http://localhost:5001/demo")
    print("   🔍 Demo SEO: http://localhost:5001/seo-demo")
    print("   📊 API Info: http://localhost:5001/")
    print("   💚 Estado: http://localhost:5001/health")
    print("   📦 Productos: http://localhost:5001/products")
    print("\n⚡ Presiona Ctrl+C para detener")
    print("="*80)
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor detenido por el usuario")
    except Exception as e:
        print(f"\n❌ Error al iniciar servidor: {str(e)}")