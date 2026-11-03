import json
import os
import re
from typing import List

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from src.core.models import ReActStep, ToolSpec
from src.core.ports import IAgentPlanner
from src.infrastructure.planners.deterministic_planner import DeterministicReActPlanner


class GeminiReActPlanner(IAgentPlanner):
    """Adaptador de producción para el bucle ReAct impulsado por Google Gemini (2.5 Flash)."""

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self._fallback = DeterministicReActPlanner()
        if HAS_GENAI and self.api_key:
            genai.configure(api_key=self.api_key)

    def decide_next_step(
        self,
        task_prompt: str,
        previous_steps: List[ReActStep],
        available_tools: List[ToolSpec],
    ) -> ReActStep:
        if not (HAS_GENAI and self.api_key):
            return self._fallback.decide_next_step(
                task_prompt, previous_steps, available_tools
            )

        step_num = len(previous_steps) + 1
        tools_desc = "\n".join(
            f"- {t.name}: {t.description} (Args: {t.parameters_hint})"
            for t in available_tools
        )
        history_desc = "\n".join(
            f"Paso {s.step_number} | Thought: {s.thought} | Tool: {s.action_tool}({s.action_input}) | Observation: {s.observation}"
            for s in previous_steps
        ) or "Sin pasos previos."

        prompt = (
            "Eres un motor autónomo ReAct (Reasoning + Acting).\n"
            "Analiza la tarea del usuario y el historial de pasos para decidir el siguiente paso.\n"
            "Si necesitas información o cálculos, elige UNA herramienta de la lista.\n"
            "Si ya tienes todas las observaciones necesarias para responder con exactitud, pon 'action_tool': null.\n\n"
            f"HERRAMIENTAS DISPONIBLES:\n{tools_desc}\n\n"
            f"HISTORIAL DE PASOS:\n{history_desc}\n\n"
            f"TAREA DEL USUARIO:\n{task_prompt}\n\n"
            "Responde EXCLUSIVAMENTE en JSON con este formato:\n"
            '{"thought": "tu razonamiento", "action_tool": "nombre_herramienta o null", "action_input": {}}'
        )

        try:
            model = genai.GenerativeModel(self.model_name)
            resp = model.generate_content(prompt)
            raw = resp.text.strip()
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                data = json.loads(match.group(0))
                return ReActStep(
                    step_number=step_num,
                    thought=str(data.get("thought", "Analizando siguiente paso...")),
                    action_tool=data.get("action_tool"),
                    action_input=data.get("action_input") or {},
                )
        except Exception:
            pass

        return self._fallback.decide_next_step(
            task_prompt, previous_steps, available_tools
        )

    def synthesize_final_answer(
        self, task_prompt: str, steps: List[ReActStep]
    ) -> str:
        if not (HAS_GENAI and self.api_key):
            return self._fallback.synthesize_final_answer(task_prompt, steps)

        obs_block = "\n".join(
            f"- Tool `{s.action_tool}`: {s.observation}"
            for s in steps
            if s.observation
        )
        prompt = (
            "Eres un Agente Empresarial de Alta Precisión.\n"
            "Responde a la tarea del usuario utilizando ÚNICAMENTE los datos de las OBSERVACIONES recolectadas.\n"
            "PROHIBIDO inventar precios, tasas, requisitos o aprobar descuentos prohibidos.\n\n"
            f"OBSERVACIONES DEL SANDBOX:\n{obs_block}\n\n"
            f"TAREA DEL USUARIO:\n{task_prompt}\n\n"
            "RESPUESTA FINAL:"
        )
        try:
            model = genai.GenerativeModel(self.model_name)
            resp = model.generate_content(prompt)
            return resp.text.strip()
        except Exception:
            return self._fallback.synthesize_final_answer(task_prompt, steps)
