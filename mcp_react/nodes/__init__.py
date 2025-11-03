"""
Nodos ReAct basados en el notebook 01_react_implementation.ipynb
Adaptados para e-commerce Hybris.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List

from ..schemas import (
    HybrisReActState, 
    ThoughtStep, 
    ActionStep, 
    ObservationStep,
    ThoughtResponse,
    ActionResponse,
    ActionType,
    build_react_trajectory
)
from ..tools import (
    search_products,
    get_product_details,
    check_stock,
    get_price_history,
    get_category_products
)

# Cargar variables de entorno
load_dotenv()

# Configurar el LLM igual que en el notebook
llm = ChatOpenAI(
    model="gpt-4-turbo-preview",
    temperature=0.0,  # Determinístico para consistencia
    api_key=os.getenv("OPENAI_API_KEY"),
)

def create_react_prompt() -> str:
    """
    Crea el prompt del sistema basado en el paper de ReAct pero para e-commerce.
    """
    return """Eres un agente ReAct especializado en consultas de productos de e-commerce Hybris que responde preguntas intercalando pasos de Pensamiento, Acción y Observación.

Tu proceso:
1. Thought: Analiza lo que sabes sobre la consulta del usuario y planea los siguientes pasos
2. Action: Ejecuta una de las acciones disponibles de e-commerce
3. Observation: Procesa los resultados obtenidos
4. Repite hasta tener la respuesta completa

Acciones disponibles para e-commerce:
- search_products[término]: Busca productos en el catálogo usando un término
- get_product_details[id]: Obtiene detalles específicos de un producto por ID
- check_stock[id]: Verifica disponibilidad de stock de un producto
- get_price_history[id]: Obtiene historial de precios de un producto
- get_category_products[categoría]: Obtiene productos de una categoría específica
- finish[respuesta]: Proporciona la respuesta final al usuario

Directrices para e-commerce:
- Siempre comienza con un pensamiento para descomponer la pregunta del usuario
- Sé específico en tus búsquedas de productos
- Usa get_product_details para obtener información detallada después de encontrar productos
- Verifica stock cuando el usuario pregunte sobre disponibilidad
- Consulta historial de precios cuando sea relevante
- Cuando estés listo para responder, tu acción debe ser finish[respuesta completa]
- Proporciona información útil como precios, disponibilidad y especificaciones"""

def build_react_messages_from_state(
    state: HybrisReActState,
    system_prompt: str,
    next_prompt: str = "¿Cuál es tu próximo pensamiento?"
) -> List:
    """
    Construye la cadena completa de mensajes para el LLM.
    Igual que en el notebook pero usando HybrisReActState.
    """
    messages = []
    
    # 1. Prompt del sistema con instrucciones ReAct
    messages.append(SystemMessage(content=system_prompt))
    
    # 2. Query original del usuario
    messages.append(HumanMessage(content=state.query))
    
    # 3. Trayectoria previa (si existe)
    trajectory = build_react_trajectory(state)
    if trajectory:
        messages.append(HumanMessage(content="\n".join(trajectory)))
    
    # 4. Prompt para el siguiente paso
    messages.append(HumanMessage(content=next_prompt))
    
    return messages

def think_node(state: HybrisReActState) -> dict:
    """
    Genera un pensamiento basado en el contexto actual.
    Basado exactamente en el think_node del notebook.
    """
    # Construir contexto
    messages = build_react_messages_from_state(
        state=state,
        system_prompt=create_react_prompt(),
        next_prompt="¿Cuál es tu próximo pensamiento? Analiza la consulta de e-commerce y planea tus siguientes pasos."
    )
    
    # Invocar LLM con salida estructurada
    llm_with_structure = llm.with_structured_output(ThoughtResponse)
    response = llm_with_structure.invoke(messages)
    
    # Actualizar estado
    step_num = state.step_counter + 1
    
    print(f"🧠 Paso {step_num} - Pensamiento: {response.thought}")
    
    # Crear nuevo pensamiento
    new_thought = ThoughtStep(content=response.thought, step_number=step_num)
    
    return {
        "thoughts": state.thoughts + [new_thought],
        "current_step_type": "think",
        "step_counter": step_num
    }

def act_node(state: HybrisReActState) -> dict:
    """
    Decide qué acción tomar basándose en el contexto.
    Basado exactamente en el act_node del notebook.
    """
    step_num = state.step_counter + 1
    
    # Construir contexto
    messages = build_react_messages_from_state(
        state=state,
        system_prompt=create_react_prompt(),
        next_prompt="¿Cuál es tu próxima acción? Elige entre: search_products[término], get_product_details[id], check_stock[id], get_price_history[id], get_category_products[categoría], o finish[respuesta]."
    )
    
    # Invocar LLM
    llm_with_structure = llm.with_structured_output(ActionResponse)
    response = llm_with_structure.invoke(messages)
    
    # Verificar límite de pasos
    if step_num > state.max_steps:
        if response.action_type != "finish":
            # Forzar terminación si excedemos el límite
            forced_action = ActionStep(
                action_type=ActionType.FINISH,
                argument="Límite de pasos alcanzado. No puedo completar la consulta de e-commerce.",
                step_number=step_num
            )
            return {
                "actions": state.actions + [forced_action],
                "should_continue": False,
                "step_counter": step_num
            }
    
    print(f"🎯 Paso {step_num} - Acción: {response.action_type}[{response.argument}]")
    
    # Crear nueva acción
    new_action = ActionStep(
        action_type=ActionType(response.action_type),
        argument=response.argument,
        step_number=step_num
    )
    
    return {
        "actions": state.actions + [new_action],
        "current_step_type": "act",
        "step_counter": step_num,
        "should_continue": response.action_type != "finish",
        "final_answer": response.argument if response.action_type == "finish" else state.final_answer
    }

def observe_node(state: HybrisReActState) -> dict:
    """
    Ejecuta la acción y genera una observación.
    Basado exactamente en el observe_node del notebook pero con herramientas de e-commerce.
    """
    if not state.actions:
        return {"current_step_type": "observe"}
    
    latest_action = state.actions[-1]
    step_num = state.step_counter
    
    # Ejecutar según el tipo de acción de e-commerce
    if latest_action.action_type == ActionType.SEARCH_PRODUCTS:
        result = search_products(latest_action.argument)
        
        # Guardar productos encontrados en contexto
        if result.get("success") and result.get("products_found"):
            if "found_products" not in state.product_context:
                state.product_context["found_products"] = []
            state.product_context["found_products"].extend(result["products_found"])
        
        observation = ObservationStep(
            content=result["content"],
            source="hybris_catalog",
            step_number=step_num
        )
        
    elif latest_action.action_type == ActionType.GET_PRODUCT_DETAILS:
        result = get_product_details(latest_action.argument)
        
        observation = ObservationStep(
            content=result["content"],
            source="hybris_product",
            step_number=step_num
        )
        
    elif latest_action.action_type == ActionType.CHECK_STOCK:
        result = check_stock(latest_action.argument)
        
        observation = ObservationStep(
            content=result["content"],
            source="hybris_inventory",
            step_number=step_num
        )
        
    elif latest_action.action_type == ActionType.GET_PRICE_HISTORY:
        result = get_price_history(latest_action.argument)
        
        observation = ObservationStep(
            content=result["content"],
            source="hybris_pricing",
            step_number=step_num
        )
        
    elif latest_action.action_type == ActionType.GET_CATEGORY_PRODUCTS:
        result = get_category_products(latest_action.argument)
        
        observation = ObservationStep(
            content=result["content"],
            source="hybris_catalog",
            step_number=step_num
        )
        
    elif latest_action.action_type == ActionType.FINISH:
        observation = ObservationStep(
            content=f"Consulta de e-commerce completada con respuesta: {latest_action.argument}",
            source="system",
            step_number=step_num
        )
    
    else:
        observation = ObservationStep(
            content=f"Tipo de acción desconocido: {latest_action.action_type}",
            source="system",
            step_number=step_num
        )
    
    print(f"👀 Paso {step_num} - Observación: {observation.content[:100]}...")
    
    return {
        "observations": state.observations + [observation],
        "current_step_type": "observe",
        "should_continue": latest_action.action_type != ActionType.FINISH,
        "product_context": state.product_context
    }