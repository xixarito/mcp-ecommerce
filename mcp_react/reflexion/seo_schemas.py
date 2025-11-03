"""
Extensión del MCP Hybris con patrón Reflexión para mejorar 
descripciones de productos automáticamente con optimización SEO.

Basado en el notebook 03_reflexion_implementation.ipynb
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# === ESTRUCTURAS DE DATOS PARA REFLEXIÓN SEO ===

class SEOCriteria(BaseModel):
    """Criterios de evaluación SEO para descripciones de productos."""
    keyword_density: int = Field(default=15, ge=0, le=20, description="Densidad de palabras clave (0-20 pts)")
    readability: int = Field(default=12, ge=0, le=15, description="Legibilidad y fluidez (0-15 pts)")
    call_to_action: int = Field(default=10, ge=0, le=15, description="Call-to-action efectivo (0-15 pts)")
    product_benefits: int = Field(default=15, ge=0, le=20, description="Beneficios del producto (0-20 pts)")
    technical_specs: int = Field(default=10, ge=0, le=15, description="Especificaciones técnicas (0-15 pts)")
    emotional_appeal: int = Field(default=12, ge=0, le=15, description="Atractivo emocional (0-15 pts)")
    
    missing_elements: List[str] = Field(default_factory=list)
    improvement_suggestions: List[str] = Field(default_factory=list)
    detected_keywords: List[str] = Field(default_factory=list)
    seo_score: Optional[int] = None
    
    # Configuración adicional para evaluación
    keyword_density_min: float = Field(default=2.0, description="Densidad mínima de keywords (%)")
    keyword_density_max: float = Field(default=5.0, description="Densidad máxima de keywords (%)")
    min_length: int = Field(default=200, description="Longitud mínima de descripción")
    max_length: int = Field(default=1500, description="Longitud máxima de descripción")
    include_call_to_action: bool = Field(default=True, description="Incluir call-to-action")
    use_structured_format: bool = Field(default=True, description="Usar formato estructurado")
    
    @property
    def total_score(self) -> int:
        return (self.keyword_density + self.readability + self.call_to_action +
                self.product_benefits + self.technical_specs + self.emotional_appeal)
    
    @property
    def feedback_summary(self) -> str:
        sections = []
        sections.append(f"SEO Score: {self.total_score}/100")
        if self.detected_keywords:
            sections.append("KEYWORDS DETECTADAS: " + ", ".join(self.detected_keywords))
        if self.missing_elements:
            sections.append("ELEMENTOS FALTANTES: " + ", ".join(self.missing_elements))
        if self.improvement_suggestions:
            sections.append("MEJORAS SEO: " + "; ".join(self.improvement_suggestions))
        return "\n".join(sections)

class SEOReflectionResponse(BaseModel):
    """Respuesta estructurada del reflector SEO."""
    lessons: List[str] = Field(
        ..., min_length=1, max_length=3,
        description="Lecciones SEO tipo 'Próxima vez, ...'"
    )

class ProductDescriptionTask(BaseModel):
    """Tarea de mejora de descripción de producto."""
    product_id: str
    original_description: str
    target_keywords: List[str]
    product_category: str
    price_range: str
    target_audience: str

# === ESTADOS PARA REFLEXIÓN SEO ===

class SEOActorState(BaseModel):
    """Estado del generador de descripciones SEO."""
    current_description: Optional[str] = None
    attempt_count: int = 0
    target_keywords: List[str] = Field(default_factory=list)

class SEOEvaluatorState(BaseModel):
    """Estado del evaluador SEO."""
    last_score: float = 0.0
    last_feedback: Optional[str] = None
    score_threshold: float = 80.0
    evaluation_history: List[dict] = Field(default_factory=list)

class SEOMemoryState(BaseModel):
    """Memoria episódica para lecciones SEO."""
    lessons: List[str] = Field(default_factory=list, max_length=3)
    memory_capacity: int = 3
    
    def add_reflections(self, new_reflections: List[str]):
        """Añade nuevas lecciones SEO manteniendo límite LIFO."""
        all_reflections = self.lessons + new_reflections
        self.lessons = all_reflections[-self.memory_capacity:]
    
    def get_memory_context(self) -> str:
        """Construye contexto de lecciones SEO para el Actor."""
        if not self.lessons:
            return "(sin lecciones SEO previas)"
        return "\nLECCIONES SEO APRENDIDAS:\n" + "\n".join(f"- {r}" for r in self.lessons)

class SEOTrajectoryState(BaseModel):
    """Registro de intentos de mejora SEO."""
    attempts: List[dict] = Field(default_factory=list)
    
    def add_attempt(self, attempt: int, description: str, score: float, feedback: str):
        """Registra un nuevo intento de descripción."""
        self.attempts.append({
            'attempt': attempt,
            'description': description,
            'score': score,
            'feedback': feedback,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_previous_context(self, limit: int = 1) -> str:
        """Obtiene contexto de intentos previos."""
        if not self.attempts:
            return ""
        
        recent = self.attempts[-limit:]
        result = []
        for attempt in recent:
            result.append(f"\nINTENTO ANTERIOR {attempt['attempt']} (Score SEO: {attempt['score']:.1f}):")
            result.append(f"Feedback: {attempt['feedback'][:150]}...")
        return "\n".join(result)

class SEOGlobalState(BaseModel):
    """Estado global para el sistema de reflexión SEO."""
    task: ProductDescriptionTask
    max_attempts: int = 3
    min_reflection_cycles: int = 1
    is_done: bool = False
    current_attempt: int = 0
    completed_reflection_cycles: int = 0
    
    def should_continue(self) -> bool:
        return not self.is_done and self.current_attempt < self.max_attempts

class SEOReflexionState(BaseModel):
    """Estado principal del sistema de reflexión SEO."""
    global_state: SEOGlobalState
    actor: SEOActorState = Field(default_factory=SEOActorState)
    evaluator: SEOEvaluatorState = Field(default_factory=SEOEvaluatorState)
    seo_memory: SEOMemoryState = Field(default_factory=SEOMemoryState)
    trajectory: SEOTrajectoryState = Field(default_factory=SEOTrajectoryState)
    
    @classmethod
    def create_initial(cls, task: ProductDescriptionTask, **kwargs):
        """Factory method para crear estado inicial."""
        return cls(
            global_state=SEOGlobalState(task=task, **kwargs)
        )

# === PROMPTS ESPECIALIZADOS EN SEO ===

class SEOPrompts:
    """Prompts especializados para optimización SEO de descripciones."""
    
    def __init__(self):
        self.actor_system_prompt = self._build_actor_prompt()
        self.evaluator_system_prompt = self._build_evaluator_prompt()
        self.reflector_system_prompt = self._build_reflector_prompt()
    
    def _build_actor_prompt(self) -> str:
        return """Eres un especialista en copywriting y SEO para e-commerce. Tu tarea es crear descripciones de productos optimizadas para SEO que conviertan visitantes en compradores.

ESTRUCTURA OBLIGATORIA:
1. **Título atractivo** (H1 con keyword principal)
2. **Descripción principal** (150-250 palabras, keywords naturalmente integradas)
3. **Beneficios clave** (3-4 puntos destacados)
4. **Especificaciones técnicas** (lista organizada)
5. **Call-to-action** (motivador y urgente)

REGLAS SEO CRÍTICAS:
- Densidad de keywords: 2-3% (natural, no spam)
- Usa sinónimos y variaciones de keywords
- Incluye beneficios emocionales y racionales
- Estructura con headers (H2, H3)
- Longitud óptima: 200-400 palabras
- Call-to-action claro y persuasivo

APLICA ESTRICTAMENTE las lecciones SEO previas."""
    
    def _build_evaluator_prompt(self) -> str:
        return """Evalúa la descripción del producto usando criterios SEO específicos:

CRITERIOS DE EVALUACIÓN:
- KEYWORD_DENSITY (0-20 pts): Uso natural de keywords sin spam
- READABILITY (0-15 pts): Fluidez, claridad, fácil lectura
- CALL_TO_ACTION (0-15 pts): CTA persuasivo y claro
- PRODUCT_BENEFITS (0-20 pts): Beneficios emocionales y racionales
- TECHNICAL_SPECS (0-15 pts): Especificaciones organizadas
- EMOTIONAL_APPEAL (0-15 pts): Conexión emocional con el usuario

DETECTA:
- Keywords principales y secundarias usadas
- Elementos faltantes para SEO
- Mejoras específicas recomendadas
- Problemas de sobre-optimización

Score total: suma de todos los criterios (máx 100 pts)."""
    
    def _build_reflector_prompt(self) -> str:
        return """Analiza el feedback SEO y genera lecciones específicas para mejorar descripciones de productos.

Genera 1-3 lecciones en formato:
- "Próxima vez, [acción específica de SEO/copywriting]"

Enfócate en:
- Optimización de keywords sin spam
- Mejora de call-to-action
- Balance entre beneficios técnicos y emocionales
- Estructura SEO-friendly
- Persuasión y conversión

Las lecciones deben ser específicas y aplicables al siguiente intento."""

# Instanciar prompts
seo_prompts = SEOPrompts()