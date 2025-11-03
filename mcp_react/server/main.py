"""
Servidor MCP principal que integra LangGraph con el patrón ReAct del notebook.
"""

from typing import Literal
from flask import Flask, request, jsonify, render_template_string
import json

# Importaciones locales
from ..schemas import HybrisReActState, create_initial_state
from ..nodes import think_node, act_node, observe_node
from ..reflexion import improve_product_description_with_reflexion

# === CONTROL DE FLUJO COMO EN EL NOTEBOOK ===

def should_continue(state: HybrisReActState) -> Literal["think", "end"]:
    """
    Determina si continuar el ciclo ReAct o terminar.
    Basado exactamente en el notebook.
    """
    # Verificar bandera de continuación
    if not state.should_continue:
        return "end"
    
    # Verificar límite de pasos
    if state.step_counter >= state.max_steps:
        return "end"
    
    # Continuar con el siguiente pensamiento
    return "think"

# === SIMULACIÓN DE LANGGRAPH ===

class SimpleGraph:
    """
    Simulación simplificada de LangGraph para el patrón ReAct.
    Como no tenemos LangGraph instalado, simulamos la funcionalidad.
    """
    
    def __init__(self):
        self.nodes = {
            "think": think_node,
            "act": act_node,
            "observe": observe_node
        }
    
    def invoke(self, initial_state: dict) -> HybrisReActState:
        """
        Ejecuta el ciclo ReAct simulando LangGraph.
        """
        # Convertir dict a HybrisReActState si es necesario
        if isinstance(initial_state, dict):
            state = HybrisReActState(**initial_state)
        else:
            state = initial_state
        
        current_node = "think"
        
        while current_node != "end" and state.step_counter < state.max_steps:
            print(f"\n--- Ejecutando nodo: {current_node} ---")
            
            # Ejecutar nodo actual
            if current_node == "think":
                updates = think_node(state)
                # Actualizar estado
                for key, value in updates.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                current_node = "act"
                
            elif current_node == "act":
                updates = act_node(state)
                # Actualizar estado
                for key, value in updates.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                current_node = "observe"
                
            elif current_node == "observe":
                updates = observe_node(state)
                # Actualizar estado
                for key, value in updates.items():
                    if hasattr(state, key):
                        setattr(state, key, value)
                
                # Decidir siguiente paso
                next_step = should_continue(state)
                current_node = next_step
        
        return state

# === SERVIDOR FLASK ===

app = Flask(__name__)
graph = SimpleGraph()

def run_react_agent(question: str) -> dict:
    """
    Ejecuta el agente ReAct con una pregunta de e-commerce.
    Basado en la función del notebook.
    """
    print(f"🚀 Iniciando agente ReAct para e-commerce...")
    print(f"📝 Pregunta: {question}\n")
    
    # Crear estado inicial
    initial_state = create_initial_state(question, max_steps=15)
    
    # Ejecutar el grafo
    result = graph.invoke(initial_state)
    
    # Mostrar resultado
    print("\n" + "="*60)
    print("🎯 RESULTADOS DEL AGENTE REACT E-COMMERCE")
    print("="*60)
    print(f"\n❓ Pregunta: {question}")
    print(f"\n💡 Respuesta Final: {result.final_answer or 'No se encontró respuesta'}")
    print(f"\n📊 Pasos realizados: {result.step_counter}")
    print("="*60)
    
    return {
        "question": question,
        "final_answer": result.final_answer,
        "steps": result.step_counter,
        "thoughts": [{"content": t.content, "step": t.step_number} for t in result.thoughts],
        "actions": [{"type": t.action_type.value, "argument": t.argument, "step": t.step_number} for t in result.actions],
        "observations": [{"content": t.content, "source": t.source, "step": t.step_number} for t in result.observations]
    }

# === ENDPOINTS API ===

@app.route('/')
def home():
    return jsonify({
        "message": "MCP Hybris E-commerce con patrón ReAct y Reflexión SEO",
        "endpoints": {
            "/query": "POST - Hacer consulta de productos",
            "/seo": "POST - Mejorar descripción de producto con reflexión SEO",
            "/demo": "GET - Interfaz web de demostración",
            "/seo-demo": "GET - Interfaz web para mejora SEO"
        }
    })

@app.route('/query', methods=['POST'])
def query_products():
    """Endpoint principal para consultas de productos."""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "Se requiere una pregunta"}), 400
        
        # Ejecutar agente ReAct
        result = run_react_agent(question)
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/seo', methods=['POST'])
def improve_seo():
    """Endpoint para mejorar descripciones de productos con reflexión SEO."""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        required_fields = ['product_id', 'original_description', 'target_keywords']
        for field in required_fields:
            if not data.get(field):
                return jsonify({"error": f"Campo requerido: {field}"}), 400
        
        # Extraer parámetros
        product_id = data['product_id']
        original_description = data['original_description']
        target_keywords = data['target_keywords'] if isinstance(data['target_keywords'], list) else [data['target_keywords']]
        
        # Parámetros opcionales
        product_category = data.get('product_category', 'General')
        price_range = data.get('price_range', 'Medio')
        target_audience = data.get('target_audience', 'General')
        max_attempts = data.get('max_attempts', 3)
        score_threshold = data.get('score_threshold', 80.0)
        
        # Ejecutar mejora SEO con reflexión
        result = improve_product_description_with_reflexion(
            product_id=product_id,
            original_description=original_description,
            target_keywords=target_keywords,
            product_category=product_category,
            price_range=price_range,
            target_audience=target_audience,
            max_attempts=max_attempts,
            score_threshold=score_threshold
        )
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/demo')
def demo():
    """Interfaz web de demostración."""
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCP Hybris E-commerce - Demo ReAct</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
                background: #f5f7fa;
            }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 30px; 
                border-radius: 10px; 
                margin-bottom: 30px;
                text-align: center;
            }
            .query-section { 
                background: white; 
                padding: 25px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            button { 
                background: #667eea; 
                color: white; 
                border: none; 
                padding: 12px 20px; 
                border-radius: 5px; 
                cursor: pointer;
                font-size: 16px;
                margin-left: 10px;
            }
            button:hover { background: #5a6fd8; }
            .results { 
                background: white; 
                padding: 25px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-top: 20px; 
            }
            .step { 
                margin: 15px 0; 
                padding: 15px; 
                border-left: 4px solid #667eea; 
                background: #f8f9ff;
            }
            .thought { border-left-color: #4CAF50; background: #f1f8e9; }
            .action { border-left-color: #ff9800; background: #fff3e0; }
            .observation { border-left-color: #2196F3; background: #e3f2fd; }
            .loading { text-align: center; color: #666; }
            .answer { 
                background: #e8f5e8; 
                padding: 20px; 
                border-radius: 8px; 
                border: 2px solid #4CAF50;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🛒 MCP Hybris E-commerce</h1>
            <p>Asistente inteligente con patrón ReAct para consultas de productos</p>
        </div>
        
        <div class="query-section">
            <h2>💬 Haz tu consulta de productos</h2>
            <input type="text" id="questionInput" placeholder="Ejemplo: ¿Cuáles son las laptops disponibles?" />
            <button onclick="askQuestion()">🔍 Consultar</button>
            
            <div class="examples">
                <h3>💡 Ejemplos de consultas:</h3>
                <button class="example-btn" onclick="setExample('¿Qué laptops están disponibles?')">Laptops disponibles</button>
                <button class="example-btn" onclick="setExample('¿Cuál es el precio del iPhone 15 Pro?')">Precio iPhone</button>
                <button class="example-btn" onclick="setExample('¿Hay stock del MacBook Air M2?')">Stock MacBook</button>
                <button class="example-btn" onclick="setExample('Muéstrame productos de electrónicos')">Electrónicos</button>
                <button class="example-btn" onclick="setExample('¿Cuál es el historial de precios de LAPTOP001?')">Historial precios</button>
            </div>
        </div>
        
        <div id="results"></div>
        
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
                
                // Intercalar pensamientos, acciones y observaciones
                const maxSteps = Math.max(data.thoughts.length, data.actions.length, data.observations.length);
                
                for (let i = 0; i < maxSteps; i++) {
                    if (i < data.thoughts.length) {
                        html += `<div class="step thought"><strong>🧠 Pensamiento ${data.thoughts[i].step}:</strong><br>${data.thoughts[i].content}</div>`;
                    }
                    if (i < data.actions.length) {
                        html += `<div class="step action"><strong>🎯 Acción ${data.actions[i].step}:</strong><br>${data.actions[i].type}[${data.actions[i].argument}]</div>`;
                    }
                    if (i < data.observations.length) {
                        html += `<div class="step observation"><strong>👀 Observación ${data.observations[i].step}:</strong><br>${data.observations[i].content}</div>`;
                    }
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
    """Interfaz web para mejora SEO de descripciones."""
    html_template = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>MCP Hybris - Mejora SEO con Reflexión</title>
        <style>
            body { 
                font-family: 'Segoe UI', Arial, sans-serif; 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
                background: #f5f7fa;
            }
            .header { 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 30px; 
                border-radius: 10px; 
                margin-bottom: 30px;
                text-align: center;
            }
            .form-section { 
                background: white; 
                padding: 25px; 
                border-radius: 10px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .form-group { margin: 15px 0; }
            .form-group label { 
                display: block; 
                margin-bottom: 5px; 
                font-weight: bold;
                color: #333;
            }
            .form-group input, .form-group textarea, .form-group select { 
                width: 100%; 
                padding: 10px; 
                border: 2px solid #ddd; 
                border-radius: 5px;
                font-size: 14px;
                box-sizing: border-box;
            }
            .form-group textarea { 
                height: 120px; 
                resize: vertical;
            }
            .form-row {
                display: flex;
                gap: 20px;
            }
            .form-row .form-group {
                flex: 1;
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
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
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
            .loading { 
                text-align: center; 
                color: #666; 
                font-size: 18px;
            }
            .lesson {
                background: #fff3e0;
                padding: 10px;
                margin: 5px 0;
                border-left: 4px solid #ff9800;
                border-radius: 4px;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🔍 Mejora SEO con Reflexión</h1>
            <p>Optimiza automáticamente las descripciones de productos para SEO</p>
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
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="product_category">Categoría:</label>
                        <select id="product_category">
                            <option value="General">General</option>
                            <option value="Electrónicos">Electrónicos</option>
                            <option value="Ropa">Ropa</option>
                            <option value="Hogar">Hogar</option>
                            <option value="Deportes">Deportes</option>
                            <option value="Salud">Salud</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="price_range">Rango de Precio:</label>
                        <select id="price_range">
                            <option value="Bajo">Bajo</option>
                            <option value="Medio" selected>Medio</option>
                            <option value="Alto">Alto</option>
                        </select>
                    </div>
                    
                    <div class="form-group">
                        <label for="target_audience">Audiencia:</label>
                        <select id="target_audience">
                            <option value="General" selected>General</option>
                            <option value="Gamers">Gamers</option>
                            <option value="Profesionales">Profesionales</option>
                            <option value="Estudiantes">Estudiantes</option>
                            <option value="Familias">Familias</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-row">
                    <div class="form-group">
                        <label for="max_attempts">Intentos Máximos:</label>
                        <input type="number" id="max_attempts" value="3" min="1" max="10" />
                    </div>
                    
                    <div class="form-group">
                        <label for="score_threshold">Umbral SEO (%):</label>
                        <input type="number" id="score_threshold" value="80" min="50" max="100" />
                    </div>
                </div>
                
                <button type="submit" class="submit-btn">🚀 Mejorar Descripción SEO</button>
            </form>
            
            <div class="examples">
                <h3>💡 Ejemplos rápidos:</h3>
                <button class="example-btn" onclick="setLaptopExample()">Laptop Gaming</button>
                <button class="example-btn" onclick="setPhoneExample()">Smartphone</button>
                <button class="example-btn" onclick="setClothingExample()">Ropa</button>
            </div>
        </div>
        
        <div id="results"></div>
        
        <script>
            function setLaptopExample() {
                document.getElementById('product_id').value = 'LAPTOP001';
                document.getElementById('original_description').value = 'Laptop para gaming con tarjeta gráfica dedicada y procesador rápido. Buena para juegos.';
                document.getElementById('target_keywords').value = 'laptop gaming, RTX 4060, Intel Core i7, gaming portátil';
                document.getElementById('product_category').value = 'Electrónicos';
                document.getElementById('target_audience').value = 'Gamers';
            }
            
            function setPhoneExample() {
                document.getElementById('product_id').value = 'PHONE001';
                document.getElementById('original_description').value = 'Teléfono inteligente con buena cámara y batería duradera.';
                document.getElementById('target_keywords').value = 'smartphone, cámara profesional, batería larga duración';
                document.getElementById('product_category').value = 'Electrónicos';
                document.getElementById('target_audience').value = 'General';
            }
            
            function setClothingExample() {
                document.getElementById('product_id').value = 'SHIRT001';
                document.getElementById('original_description').value = 'Camisa de algodón cómoda y fresca para el verano.';
                document.getElementById('target_keywords').value = 'camisa algodón, ropa verano, moda casual';
                document.getElementById('product_category').value = 'Ropa';
                document.getElementById('target_audience').value = 'General';
            }
            
            document.getElementById('seoForm').addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = {
                    product_id: document.getElementById('product_id').value,
                    original_description: document.getElementById('original_description').value,
                    target_keywords: document.getElementById('target_keywords').value.split(',').map(k => k.trim()),
                    product_category: document.getElementById('product_category').value,
                    price_range: document.getElementById('price_range').value,
                    target_audience: document.getElementById('target_audience').value,
                    max_attempts: parseInt(document.getElementById('max_attempts').value),
                    score_threshold: parseFloat(document.getElementById('score_threshold').value)
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
                html += `<div class="metric">Ciclos Reflexión: ${data.reflection_cycles}</div>`;
                html += `<div class="metric">Estado: ${data.success ? '✅ Aprobado' : '❌ Pendiente'}</div>`;
                html += '</div>';
                
                // Comparación antes/después
                if (data.improved_description) {
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
                }
                
                // Lecciones aprendidas
                if (data.seo_lessons && data.seo_lessons.length > 0) {
                    html += '<h3>🎓 Lecciones SEO Aprendidas:</h3>';
                    data.seo_lessons.forEach((lesson, i) => {
                        html += `<div class="lesson">${i + 1}. ${lesson}</div>`;
                    });
                }
                
                // Historial de evaluaciones
                if (data.evaluation_history && data.evaluation_history.length > 0) {
                    html += '<h3>📈 Evolución del Score SEO:</h3>';
                    html += '<div class="metrics">';
                    data.evaluation_history.forEach(eval => {
                        html += `<div class="metric">Intento ${eval.attempt}: ${eval.score.toFixed(1)}/100</div>`;
                    });
                    html += '</div>';
                }
                
                // Feedback final
                if (data.final_feedback) {
                    html += '<h3>💬 Feedback Final del Evaluador:</h3>';
                    html += `<div class="metrics"><p>${data.final_feedback}</p></div>`;
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
    print("🚀 Iniciando servidor MCP Hybris E-commerce con ReAct y Reflexión SEO...")
    print("📱 Demo ReAct disponible en: http://localhost:5001/demo")
    print("� Demo SEO disponible en: http://localhost:5001/seo-demo")
    print("🔗 API disponible en: http://localhost:5001/query y http://localhost:5001/seo")
    app.run(host='0.0.0.0', port=5001, debug=True)