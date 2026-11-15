import os
import threading
from typing import Optional

try:
    import google.generativeai as genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

from src.core.models import AgentTrajectory, EvalReport, GoldenTestCase
from src.core.ports import IEvalJudge
from src.infrastructure.judges.deterministic_judge import DeterministicEvalJudge

_JUDGE_LOCK = threading.Lock()


class CloudEvalJudge(IEvalJudge):
    """
    Adaptador híbrido LLM-as-a-Judge en la nube con aislamiento efímero de API Key.
    """

    def __init__(
        self,
        api_key: str | None = None,
        model_name: str = "gemini-2.5-flash",
    ) -> None:
        self._api_key = (
            api_key or os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY", "")
        ).strip()
        self.model_name = model_name
        self._deterministic = DeterministicEvalJudge()

    def __repr__(self) -> str:
        return f"<CloudEvalJudge model={self.model_name} key=REDACTED>"

    def evaluate_trajectory(
        self,
        trajectory: AgentTrajectory,
        golden_case: Optional[GoldenTestCase] = None,
    ) -> EvalReport:
        base_report = self._deterministic.evaluate_trajectory(trajectory, golden_case)
        if not (HAS_GENAI and self._api_key):
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
        with _JUDGE_LOCK:
            try:
                genai.configure(api_key=self._api_key)
                model = genai.GenerativeModel(self.model_name)
                resp = model.generate_content(prompt)
                if resp.text:
                    base_report.judge_summary = f"{base_report.judge_summary}\n\n🤖 **Dictamen LLM-as-a-Judge ({self.model_name}):** {resp.text.strip()}"
            except Exception:
                pass
            finally:
                genai.configure(api_key="cleared")

        return base_report
