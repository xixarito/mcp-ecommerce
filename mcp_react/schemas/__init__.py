"""
Schemas para el MCP Hybris basado en el patrón ReAct del notebook.
Combina las estructuras del notebook con modelos específicos de e-commerce.
"""

from typing import Optional, List, Annotated, Dict, Any, Literal
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, field_validator
import operator

# === TIPOS BASE DEL NOTEBOOK ===

class ActionType(str, Enum):
    """Acciones que el agente puede ejecutar en e-commerce."""
    SEARCH_PRODUCTS = "search_products"
    GET_PRODUCT_DETAILS = "get_product_details"
    CHECK_STOCK = "check_stock"
    GET_PRICE_HISTORY = "get_price_history"
    GET_CATEGORY_PRODUCTS = "get_category_products"
    FINISH = "finish"

# === ESTRUCTURAS DE DATOS PRINCIPALES ===

@dataclass
class ThoughtStep:
    """
    Representa un paso de razonamiento en el patrón ReAct.
    El agente usa estos pensamientos para planear sus próximas acciones.
    """
    content: str
    step_number: int
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class ActionStep:
    """
    Representa una acción concreta tomada por el agente.
    Por ejemplo: search_products[laptop] o finish[respuesta final]
    """
    action_type: ActionType
    argument: str
    step_number: int
    timestamp: Optional[datetime] = None
    
@dataclass
class ObservationStep:
    """
    Representa el resultado de ejecutar una acción.
    Contiene la información obtenida y metadatos sobre la fuente.
    """
    content: str
    source: str  # hybris, cache, etc.
    step_number: int
    timestamp: Optional[datetime] = None

# === MODELOS DE RESPUESTA ESTRUCTURADA ===

class ThoughtResponse(BaseModel):
    """Modelo para parsear los pensamientos del LLM."""
    thought: str = Field(
        ..., 
        description="El contenido del pensamiento del agente sobre productos.",
        min_length=1,
    )
    
    @field_validator("thought")
    @classmethod
    def thought_not_empty(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("El pensamiento no puede estar vacío.")
        return value.strip()

class ActionResponse(BaseModel):
    """Modelo para parsear las decisiones de acción del LLM."""
    action_type: Literal[
        "search_products", 
        "get_product_details", 
        "check_stock", 
        "get_price_history",
        "get_category_products",
        "finish"
    ] = Field(
        ..., 
        description="Tipo de acción a realizar en e-commerce.",
    )
    argument: str = Field(
        ..., 
        description="Argumento para la acción (término de búsqueda, ID producto, etc.).",
        min_length=1,
    )

# === MODELOS ESPECÍFICOS DE E-COMMERCE ===

class ProductModel(BaseModel):
    """Modelo de producto para Hybris."""
    id: str
    name: str
    description: str
    price: float
    currency: str = "MXN"
    category: str
    brand: str
    stock: int
    rating: float = Field(ge=0, le=5)
    image_url: Optional[str] = None
    specifications: Dict[str, Any] = Field(default_factory=dict)

class SearchResultModel(BaseModel):
    """Resultado de búsqueda de productos."""
    products: List[ProductModel]
    total_results: int
    page: int = 1
    per_page: int = 10
    query: str

class StockInfo(BaseModel):
    """Información de stock de un producto."""
    product_id: str
    available: bool
    quantity: int
    warehouse: str = "main"
    last_updated: datetime = Field(default_factory=datetime.now)

class PriceHistory(BaseModel):
    """Historial de precios de un producto."""
    product_id: str
    prices: List[Dict[str, Any]]  # [{"date": "2024-01-01", "price": 999.99}]
    current_price: float
    lowest_price: float
    highest_price: float

# === ESTADO REACT PARA E-COMMERCE ===

class HybrisReActState(BaseModel):
    """
    Estado completo del agente ReAct para e-commerce Hybris.
    Basado en ReActState del notebook pero adaptado para productos.
    """
    # Query original del usuario
    query: str
    
    # Trayectoria de razonamiento (se acumula)
    thoughts: List[ThoughtStep] = Field(default_factory=list)
    actions: List[ActionStep] = Field(default_factory=list)
    observations: List[ObservationStep] = Field(default_factory=list)
    
    # Control de flujo
    current_step_type: Optional[str] = None  # 'think', 'act', 'observe', 'finish'
    step_counter: int = 0
    max_steps: int = 15
    should_continue: bool = True
    
    # Contexto específico de e-commerce
    product_context: Dict[str, Any] = Field(default_factory=dict)  # Para mantener productos encontrados
    search_history: List[str] = Field(default_factory=list)  # Términos buscados
    
    # Resultado final
    final_answer: Optional[str] = None

# === FUNCIONES DE UTILIDAD ===

def create_initial_state(query: str, max_steps: int = 15) -> HybrisReActState:
    """
    Crea el estado inicial para una nueva consulta de e-commerce.
    """
    return HybrisReActState(
        query=query,
        max_steps=max_steps,
        should_continue=True
    )

def build_react_trajectory(state: HybrisReActState) -> List[str]:
    """
    Construye la trayectoria cronológica de eventos.
    Intercala pensamientos, acciones y observaciones en el orden correcto.
    """
    trajectory = []
    max_steps = max(
        len(state.thoughts), 
        len(state.actions), 
        len(state.observations)
    )
    
    for i in range(max_steps):
        # Agregar pensamiento si existe
        if i < len(state.thoughts):
            thought = state.thoughts[i]
            trajectory.append(f"Thought: {thought.content}")
            
        # Agregar acción si existe  
        if i < len(state.actions):
            action = state.actions[i]
            trajectory.append(f"Action: {action.action_type}[{action.argument}]")
            
        # Agregar observación si existe
        if i < len(state.observations):
            obs = state.observations[i]
            trajectory.append(f"Observation: {obs.content}")
    
    return trajectory