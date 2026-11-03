import os
from typing import Optional

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from src.core.models import AgentTrajectory, EvalReport, GoldenTestCase
from src.core.ports import IEvalJudge
from src.infrastructure.judges.deterministic_judge import DeterministicEvalJudge


class GeminiEvalJudge(IEvalJudge):
    """
    Adaptador híbrido LLM-as-a-Judge con Google Gemini 2.5 Flash:
    Combina la verificación matemática de no-alucinación con un dictamen cualitativo de Gemini.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self._deterministic = DeterministicEvalJudge()
        if HAS_GENAI and self.api_key:
            genai.configure(api_key=self.api_key)

    def evaluate_trajectory(
        self,
        trajectory: AgentTrajectory,
        golden_case: Optional[GoldenTestCase] = None,
    ) -> EvalReport:
        base_report = self._deterministic.evaluate_trajectory(trajectory, golden_case)
        if not (HAS_GENAI and self.api_key):
            return base_report

        obs_text = "\n".join(
            f"- {s.action_tool}: {s.observation}"
            for s in trajectory.steps
            if s.observation
        )
        prompt = (
            "Actúa como un Juez Auditor Senior de IA (LLM-as-a-Judge).\n"
            "Evalúa en 2 oraciones ejecutivas la calidad técnica de la respuesta del agente comparándola con las observaciones.\n\n"
            f"PREGUNTA: {trajectory.task_prompt}\n"
            f"OBSERVACIONES: {obs_text}\n"
            f"RESPUESTA DEL AGENTE: {trajectory.final_answer}\n"
            f"VEREDICTO MATEMÁTICO: {base_report.verdict.value} (Score: {base_report.overall_score})\n\n"
            "DICTAMEN EJECUTIVO:"
        )
        try:
            model = genai.GenerativeModel(self.model_name)
            resp = model.generate_content(prompt)
            if resp.text:
                base_report.judge_summary = f"{base_report.judge_summary}\n\n🤖 **Dictamen LLM-as-a-Judge ({self.model_name}):** {resp.text.strip()}"
        except Exception:
            pass

        return base_report
