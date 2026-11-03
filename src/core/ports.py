from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from src.core.models import (
    AgentTrajectory,
    EvalReport,
    GoldenTestCase,
    ReActStep,
    ToolSpec,
)


class IToolSandbox(ABC):
    """Puerto para el entorno aislado de ejecución de herramientas del Agente (Sandbox)."""

    @abstractmethod
    def list_available_tools(self) -> List[ToolSpec]:
        """Devuelve el catálogo de herramientas permitidas en el Sandbox."""
        pass

    @abstractmethod
    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Ejecuta una herramienta de forma segura y devuelve su observación como texto."""
        pass


class IAgentPlanner(ABC):
    """Puerto para el motor de razonamiento ReAct (Thought -> Action -> Final Answer)."""

    @abstractmethod
    def decide_next_step(
        self,
        task_prompt: str,
        previous_steps: List[ReActStep],
        available_tools: List[ToolSpec],
    ) -> ReActStep:
        """Decide el siguiente pensamiento y qué herramienta invocar (o ninguno si ya tiene la respuesta)."""
        pass

    @abstractmethod
    def synthesize_final_answer(
        self, task_prompt: str, steps: List[ReActStep]
    ) -> str:
        """Construye la respuesta final al usuario basándose estrictamente en las observaciones recolectadas."""
        pass


class IEvalJudge(ABC):
    """Puerto para el Juez Evaluador (LLM-as-a-Judge / Auditor Determinista de Calidad y Alucinaciones)."""

    @abstractmethod
    def evaluate_trajectory(
        self,
        trajectory: AgentTrajectory,
        golden_case: Optional[GoldenTestCase] = None,
    ) -> EvalReport:
        """Evalúa una ejecución completa del agente y emite puntajes de Fidelidad, Herramientas, Relevancia y Seguridad."""
        pass
