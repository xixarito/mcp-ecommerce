"""
Grafo de reflexión SEO y servidor para mejorar descripciones de productos.
"""

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("⚠️ LangGraph no disponible - usando simulación")

from .seo_schemas import SEOReflexionState, ProductDescriptionTask
from .seo_nodes import seo_actor, seo_evaluator, seo_reflector, route_after_seo_eval

class SimpleReflexionGraph:
    """Simulación simplificada del grafo de reflexión SEO."""
    
    def __init__(self):
        self.nodes = {
            "seo_actor": seo_actor,
            "seo_evaluator": seo_evaluator,
            "seo_reflector": seo_reflector
        }
    
    def invoke(self, initial_state: SEOReflexionState) -> SEOReflexionState:
        """Ejecuta el ciclo de reflexión SEO."""
        state = initial_state
        current_node = "seo_actor"
        
        while current_node != "END" and state.global_state.current_attempt < state.global_state.max_attempts:
            print(f"\n--- Ejecutando nodo SEO: {current_node} ---")
            
            if current_node == "seo_actor":
                state = seo_actor(state)
                current_node = "seo_evaluator"
                
            elif current_node == "seo_evaluator":
                state = seo_evaluator(state)
                next_step = route_after_seo_eval(state)
                current_node = next_step if next_step != "END" else "END"
                
            elif current_node == "seo_reflector":
                state = seo_reflector(state)
                current_node = "seo_actor"
        
        return state

def build_seo_reflexion_graph():
    """Construye el grafo de reflexión SEO."""
    print("🔧 Construyendo grafo de reflexión SEO...")
    
    if LANGGRAPH_AVAILABLE:
        # Usar LangGraph real
        builder = StateGraph(SEOReflexionState)
        
        # Agregar nodos
        builder.add_node("seo_actor", seo_actor)
        builder.add_node("seo_evaluator", seo_evaluator)
        builder.add_node("seo_reflector", seo_reflector)
        
        # Configurar flujo
        builder.set_entry_point("seo_actor")
        builder.add_edge("seo_actor", "seo_evaluator")
        builder.add_edge("seo_reflector", "seo_actor")
        
        # Edge condicional desde evaluador
        builder.add_conditional_edges(
            "seo_evaluator",
            route_after_seo_eval,
            {
                "reflect": "seo_reflector",
                "END": END
            }
        )
        
        compiled_graph = builder.compile()
        print("✅ Grafo LangGraph compilado exitosamente")
        return compiled_graph
    else:
        # Usar simulación
        graph = SimpleReflexionGraph()
        print("✅ Grafo simulado creado exitosamente")
        return graph

def improve_product_description_with_reflexion(
    product_id: str,
    original_description: str,
    target_keywords: list,
    product_category: str = "General",
    price_range: str = "Medio",
    target_audience: str = "General",
    max_attempts: int = 3,
    score_threshold: float = 80.0
) -> dict:
    """
    Mejora una descripción de producto usando reflexión SEO.
    
    Args:
        product_id: ID del producto
        original_description: Descripción original
        target_keywords: Lista de palabras clave objetivo
        product_category: Categoría del producto
        price_range: Rango de precio (Bajo/Medio/Alto)
        target_audience: Audiencia objetivo
        max_attempts: Intentos máximos
        score_threshold: Umbral de calidad SEO
    
    Returns:
        dict: Resultados con descripción mejorada y métricas
    """
    print("\n" + "="*70)
    print("🔍 SISTEMA DE REFLEXIÓN SEO - MEJORA DE DESCRIPCIONES")
    print("="*70)
    
    # Crear tarea de mejora
    task = ProductDescriptionTask(
        product_id=product_id,
        original_description=original_description,
        target_keywords=target_keywords,
        product_category=product_category,
        price_range=price_range,
        target_audience=target_audience
    )
    
    print(f"\n📦 Producto: {product_id}")
    print(f"🎯 Keywords: {', '.join(target_keywords)}")
    print(f"📊 Umbral SEO: {score_threshold}/100")
    print(f"🔄 Intentos máximos: {max_attempts}")
    print("\n" + "-"*50)
    
    # Crear estado inicial
    initial_state = SEOReflexionState.create_initial(
        task=task,
        max_attempts=max_attempts
    )
    initial_state.evaluator.score_threshold = score_threshold
    
    # Construir y ejecutar grafo
    graph = build_seo_reflexion_graph()
    
    try:
        print("\n🚀 Ejecutando reflexión SEO...")
        print("-"*50)
        
        final_state = graph.invoke(initial_state)
        
        # Procesar resultados
        if isinstance(final_state, dict):
            final_state = SEOReflexionState(**final_state)
        
        # Mostrar resultados
        print("\n" + "="*70)
        print("📊 RESULTADOS DE REFLEXIÓN SEO")
        print("="*70)
        
        success = final_state.global_state.is_done
        score = final_state.evaluator.last_score
        attempts = final_state.global_state.current_attempt
        cycles = final_state.global_state.completed_reflection_cycles
        
        status = "✅ DESCRIPCIÓN SEO APROBADA" if success else "❌ REQUIERE MÁS TRABAJO"
        print(f"\nEstado: {status}")
        print(f"Score SEO final: {score:.1f}/100")
        print(f"Intentos utilizados: {attempts}/{max_attempts}")
        print(f"Ciclos de reflexión: {cycles}")
        
        # Mostrar lecciones SEO aprendidas
        if final_state.seo_memory.lessons:
            print(f"\n🎓 LECCIONES SEO APRENDIDAS ({len(final_state.seo_memory.lessons)}):")
            for i, lesson in enumerate(final_state.seo_memory.lessons, 1):
                print(f"  {i}. {lesson}")
        
        # Mostrar evolución de scores SEO
        if final_state.evaluator.evaluation_history:
            print("\n📈 EVOLUCIÓN DE SCORES SEO:")
            for eval_record in final_state.evaluator.evaluation_history:
                print(f"  Intento {eval_record['attempt']}: {eval_record['score']:.1f}/100")
        
        # Mostrar comparación antes/después
        print(f"\n📄 COMPARACIÓN ANTES/DESPUÉS:")
        print("-"*50)
        print("🔴 DESCRIPCIÓN ORIGINAL:")
        print(f"  {original_description[:200]}...")
        
        if final_state.actor.current_description:
            print("\n🟢 DESCRIPCIÓN SEO MEJORADA:")
            improved_lines = final_state.actor.current_description.split('\n')[:10]
            for line in improved_lines:
                if line.strip():
                    print(f"  {line}")
            if len(final_state.actor.current_description.split('\n')) > 10:
                print(f"  ... ({len(final_state.actor.current_description)} caracteres totales)")
        
        # Preparar resultado
        result = {
            "success": success,
            "seo_score": score,
            "attempts_used": attempts,
            "reflection_cycles": cycles,
            "original_description": original_description,
            "improved_description": final_state.actor.current_description,
            "seo_lessons": final_state.seo_memory.lessons,
            "evaluation_history": final_state.evaluator.evaluation_history,
            "final_feedback": final_state.evaluator.last_feedback
        }
        
        return result
        
    except Exception as e:
        print(f"\n❌ Error durante reflexión SEO: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "original_description": original_description
        }