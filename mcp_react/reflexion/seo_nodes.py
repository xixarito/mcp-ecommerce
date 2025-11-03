"""
Nodos de reflexión SEO para mejorar descripciones de productos.
Implementa el patrón Actor → Evaluador → Reflector especializado en SEO.
"""

import os
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import Literal

from .seo_schemas import (
    SEOReflexionState, 
    SEOCriteria,
    SEOReflectionResponse,
    seo_prompts
)

# Cargar variables de entorno
load_dotenv()

# Configurar LLM
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.1,  # Baja temperatura para consistencia en SEO
    api_key=os.getenv("OPENAI_API_KEY"),
)

def seo_actor(state: SEOReflexionState) -> SEOReflexionState:
    """
    Nodo Actor SEO: Genera descripciones de productos optimizadas.
    
    Flujo:
    1. Incrementa contador de intentos
    2. Obtiene lecciones SEO de memoria episódica
    3. Genera nueva descripción con LLM
    4. Actualiza estado
    """
    # Incrementar intento
    new_global_state = state.global_state.model_copy()
    new_global_state.current_attempt += 1
    
    print(f"🎭 Generando descripción SEO - Intento {new_global_state.current_attempt}")
    
    try:
        task = state.global_state.task
        
        # Construir contexto SEO
        memory_context = state.seo_memory.get_memory_context()
        previous_context = state.trajectory.get_previous_context()
        
        # Construir prompt especializado en SEO
        user_content = f"""PRODUCTO A OPTIMIZAR:
ID: {task.product_id}
Descripción original: {task.original_description}
Keywords objetivo: {', '.join(task.target_keywords)}
Categoría: {task.product_category}
Rango de precio: {task.price_range}
Audiencia: {task.target_audience}

{memory_context}
{previous_context}

Genera una descripción SEO-optimizada que mejore conversiones y ranking."""

        messages = [
            SystemMessage(content=seo_prompts.actor_system_prompt),
            HumanMessage(content=user_content)
        ]
        
        # Generar descripción SEO
        response = llm.invoke(messages)
        description = response.content or ""
        
        if not description.strip():
            raise ValueError("LLM retornó descripción vacía")
        
        print(f"✅ Descripción SEO generada ({len(description)} caracteres)")
        
    except Exception as e:
        # Fallback con descripción básica
        task = state.global_state.task
        description = f"""# {task.product_id} - Descripción SEO Mejorada

{task.original_description}

**Palabras clave:** {', '.join(task.target_keywords)}

*Nota: Error en generación: {str(e)}*"""
        print(f"⚠️ Error en Actor SEO, usando fallback: {e}")
    
    # Actualizar estado
    new_actor = state.actor.model_copy()
    new_actor.current_description = description
    new_actor.attempt_count += 1
    new_actor.target_keywords = state.global_state.task.target_keywords
    
    return state.model_copy(update={
        "global_state": new_global_state,
        "actor": new_actor
    })

def seo_evaluator(state: SEOReflexionState) -> SEOReflexionState:
    """
    Nodo Evaluador SEO: Evalúa descripciones con criterios SEO específicos.
    
    Flujo:
    1. Evalúa descripción con criterios SEO
    2. Registra intento en trayectoria
    3. Determina si continuar o terminar
    """
    print(f"⚖️ Evaluando calidad SEO de la descripción")
    
    # Validar contenido
    description = state.actor.current_description or ""
    if not description.strip():
        score, feedback = 0.0, "No hay descripción para evaluar"
        print(f"⚠️ Descripción vacía")
    else:
        # Construir prompt de evaluación SEO
        task = state.global_state.task
        user_content = f"""EVALÚA ESTA DESCRIPCIÓN SEO:

PRODUCTO:
- ID: {task.product_id}
- Keywords objetivo: {', '.join(task.target_keywords)}
- Categoría: {task.product_category}
- Audiencia: {task.target_audience}

DESCRIPCIÓN A EVALUAR:
{description}

DESCRIPCIÓN ORIGINAL (para comparar):
{task.original_description}

Evalúa según criterios SEO y asigna puntuación detallada."""

        messages = [
            SystemMessage(content=seo_prompts.evaluator_system_prompt),
            HumanMessage(content=user_content)
        ]
        
        try:
            llm_with_structure = llm.with_structured_output(SEOCriteria)
            evaluation = llm_with_structure.invoke(messages)
            
            # Validar score
            score = float(evaluation.total_score)
            if not (0 <= score <= 100):
                raise ValueError(f"Score SEO fuera de rango: {score}")
            
            feedback = evaluation.feedback_summary
            print(f"📊 Score SEO: {score:.1f}/100")
            
        except Exception as e:
            score, feedback = 0.0, f"Error en evaluación SEO: {str(e)}"
            print(f"❌ Error evaluando SEO: {e}")
    
    # Registrar intento
    try:
        state.trajectory.add_attempt(
            state.global_state.current_attempt,
            description,
            score,
            feedback
        )
    except Exception as e:
        print(f"⚠️ Error registrando intento SEO: {e}")
    
    # Actualizar estado del evaluador
    new_evaluator = state.evaluator.model_copy()
    new_evaluator.last_score = score
    new_evaluator.last_feedback = feedback
    new_evaluator.evaluation_history.append({
        'attempt': state.global_state.current_attempt,
        'score': score,
        'feedback': feedback,
        'timestamp': datetime.now().isoformat()
    })
    
    updates = {"evaluator": new_evaluator, "trajectory": state.trajectory}
    
    # Verificar si alcanzó el umbral SEO
    if score >= state.evaluator.score_threshold:
        print(f"🎉 Descripción SEO aprobada! Score: {score:.1f}/100")
        updates["global_state"] = state.global_state.model_copy(update={"is_done": True})
    else:
        threshold = state.evaluator.score_threshold
        print(f"📉 Descripción SEO requiere mejoras: {score:.1f}/{threshold}")
    
    return state.model_copy(update=updates)

def seo_reflector(state: SEOReflexionState) -> SEOReflexionState:
    """
    Nodo Reflector SEO: Analiza fallos y genera lecciones SEO específicas.
    
    Flujo:
    1. Analiza descripción fallida y feedback SEO
    2. Genera 1-3 lecciones SEO prescriptivas
    3. Actualiza memoria episódica SEO
    """
    cycle_num = state.global_state.completed_reflection_cycles + 1
    print(f"🤔 Iniciando auto-reflexión SEO - Ciclo {cycle_num}")
    
    try:
        task = state.global_state.task
        
        # Construir contexto de reflexión SEO
        user_content = f"""ANALIZA ESTE CASO SEO:

PRODUCTO:
- ID: {task.product_id}
- Keywords objetivo: {', '.join(task.target_keywords)}
- Categoría: {task.product_category}

DESCRIPCIÓN GENERADA:
{state.actor.current_description or ""}

FEEDBACK SEO DETALLADO:
{state.evaluator.last_feedback or ""}

SCORE SEO: {state.evaluator.last_score}/100

LECCIONES SEO PREVIAS:
{state.seo_memory.get_memory_context()}

Genera lecciones específicas para mejorar el SEO y conversión en el próximo intento."""

        messages = [
            SystemMessage(content=seo_prompts.reflector_system_prompt),
            HumanMessage(content=user_content)
        ]
        
        # Generar reflexión SEO
        llm_with_structure = llm.with_structured_output(SEOReflectionResponse)
        reflection = llm_with_structure.invoke(messages)
        
        # Validar lecciones SEO
        lessons = reflection.lessons
        if not lessons or not isinstance(lessons, list):
            raise ValueError("No se generaron lecciones SEO válidas")
        
        # Validar formato de lecciones SEO
        valid_lessons = []
        for lesson in lessons:
            if isinstance(lesson, str) and lesson.strip():
                if not lesson.startswith("Próxima vez"):
                    lesson = f"Próxima vez, {lesson}"
                valid_lessons.append(lesson)
        
        if not valid_lessons:
            raise ValueError("Ninguna lección SEO tiene formato válido")
        
        lessons = valid_lessons
        print(f"🎓 Lecciones SEO generadas: {len(lessons)}")
        
    except Exception as e:
        # Fallback con lección SEO genérica
        lessons = [f"Próxima vez, revisar criterios SEO básicos: {str(e)}"]
        print(f"⚠️ Error en reflexión SEO, usando fallback: {e}")
    
    # Actualizar memoria episódica SEO
    try:
        new_memory = state.seo_memory.model_copy()
        new_memory.add_reflections(lessons)
        print(f"💾 Memoria SEO actualizada - Total lecciones: {len(new_memory.lessons)}")
    except Exception as e:
        print(f"⚠️ Error actualizando memoria SEO: {e}")
        new_memory = state.seo_memory  # Mantener estado anterior
    
    return state.model_copy(update={
        "seo_memory": new_memory,
        "global_state": state.global_state.model_copy(update={
            "completed_reflection_cycles": state.global_state.completed_reflection_cycles + 1
        })
    })

def route_after_seo_eval(state: SEOReflexionState) -> Literal["reflect", "END"]:
    """
    Decide el próximo paso después de evaluar SEO.
    
    Prioridades:
    1. Si alcanzó límite de intentos → END
    2. Si necesita reflexión mínima → reflect
    3. Si aprobó con reflexión cumplida → END
    4. Si falló → reflect
    """
    gs = state.global_state
    
    # Límite de intentos alcanzado
    if gs.current_attempt >= gs.max_attempts:
        print(f"🛑 Límite de intentos SEO alcanzado: {gs.current_attempt}/{gs.max_attempts}")
        return "END"
    
    # Garantizar reflexión mínima
    if gs.completed_reflection_cycles < gs.min_reflection_cycles:
        remaining = gs.min_reflection_cycles - gs.completed_reflection_cycles
        print(f"🔄 Reflexión SEO obligatoria - Ciclos restantes: {remaining}")
        return "reflect"
    
    # Éxito con reflexión cumplida
    if gs.is_done:
        print(f"✅ Descripción SEO exitosa")
        return "END"
    
    # Continuar mejorando SEO
    print(f"🔄 Continuando mejora SEO")
    return "reflect"