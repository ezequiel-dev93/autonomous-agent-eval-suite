from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AgentStopReason(str, Enum):
    COMPLETED = "COMPLETED"                    # El agente resolvió la tarea con éxito
    MAX_STEPS_REACHED = "MAX_STEPS_REACHED"    # Cortacircuitos activado por límite de pasos
    GUARDRAIL_BLOCKED = "GUARDRAIL_BLOCKED"    # Bloqueado por intento de violación de seguridad / política
    TOOL_ERROR = "TOOL_ERROR"                  # Error irrecuperable en herramienta


class EvalVerdict(str, Enum):
    PASS = "PASS"          # Aprobado para producción (Cumple umbral de calidad y 0% alucinación)
    WARN = "WARN"          # Aprobado con advertencias menores de eficiencia
    FAIL = "FAIL"          # Rechazado (Alucinación detectada, herramienta incorrecta o violación de política)


class ToolSpec(BaseModel):
    name: str = Field(description="Nombre único de la herramienta en snake_case")
    description: str = Field(description="Descripción clara de qué hace y cuándo usarla")
    parameters_hint: str = Field(description="Ejemplo o esquema de argumentos esperados")


class ReActStep(BaseModel):
    step_number: int = Field(description="Número secuencial del paso dentro del bucle ReAct")
    thought: str = Field(description="Razonamiento interno del agente (Thought)")
    action_tool: Optional[str] = Field(
        default=None,
        description="Herramienta invocada en este paso (None si ya emite la respuesta final)",
    )
    action_input: Dict[str, Any] = Field(
        default_factory=dict, description="Argumentos estructurados enviados a la herramienta"
    )
    observation: Optional[str] = Field(
        default=None, description="Resultado determinista devuelto por el Sandbox (Observation)"
    )
    latency_ms: float = Field(default=0.0, description="Tiempo de ejecución del paso en milisegundos")


class AgentTrajectory(BaseModel):
    task_prompt: str = Field(description="Misión o pregunta original del usuario")
    steps: List[ReActStep] = Field(
        default_factory=list, description="Traza completa de pasos Thought -> Action -> Observation"
    )
    final_answer: str = Field(description="Respuesta final consolidada por el agente")
    stop_reason: AgentStopReason = Field(
        default=AgentStopReason.COMPLETED, description="Razón por la cual finalizó el bucle"
    )
    total_latency_ms: float = Field(default=0.0, description="Latencia total de la ejecución en ms")
    estimated_tokens: int = Field(default=0, description="Tokens totales estimados consumidos")
    estimated_cost_usd: float = Field(default=0.0, description="Costo estimado en USD")
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Marca de tiempo UTC de la ejecución",
    )


class EvalMetricScore(BaseModel):
    metric_name: str = Field(
        description="Nombre de la métrica (Faithfulness, Tool Accuracy, Answer Relevance, Safety Guardrail)"
    )
    score: float = Field(ge=0.0, le=1.0, description="Puntaje normalizado entre 0.0 y 1.0")
    passed: bool = Field(description="Indica si superó el umbral mínimo exigido")
    reason: str = Field(description="Justificación técnica auditable del juez")


class EvalReport(BaseModel):
    trajectory: AgentTrajectory = Field(description="Traza del agente que fue auditada")
    metrics: List[EvalMetricScore] = Field(
        default_factory=list, description="Desglose de métricas cuantitativas"
    )
    overall_score: float = Field(ge=0.0, le=1.0, description="Promedio ponderado de calidad")
    verdict: EvalVerdict = Field(description="Veredicto final del Quality Gate (PASS, WARN, FAIL)")
    hallucination_detected: bool = Field(
        default=False, description="True si se detectaron cifras o datos no respaldados por observaciones"
    )
    judge_summary: str = Field(description="Dictamen ejecutivo del Juez Evaluador")


class GoldenTestCase(BaseModel):
    case_id: str = Field(description="Identificador del caso de prueba (ej. EVAL-AUTO-01)")
    category: str = Field(description="Categoría (Finanzas Automotriz, Triaje Clínico, Seguridad / Red-Teaming)")
    prompt: str = Field(description="Entrada de prueba para el agente")
    expected_tools: List[str] = Field(
        default_factory=list, description="Herramientas que el agente DEBE invocar"
    )
    expected_keywords: List[str] = Field(
        default_factory=list, description="Datos o cifras exactas que deben figurar en la respuesta"
    )
    forbidden_keywords: List[str] = Field(
        default_factory=list, description="Palabras o promesas prohibidas (ej. descuentos ilegales)"
    )


class BenchmarkCaseResult(BaseModel):
    test_case: GoldenTestCase
    eval_report: EvalReport


class BenchmarkSuiteResult(BaseModel):
    suite_name: str = Field(default="Enterprise Agent Readiness Suite v1.0")
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate_pct: float
    avg_faithfulness: float
    avg_tool_accuracy: float
    avg_safety_score: float
    avg_latency_ms: float
    total_cost_usd: float
    results: List[BenchmarkCaseResult] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
