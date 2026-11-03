import time
from typing import List, Optional
from src.core.models import (
    AgentStopReason,
    AgentTrajectory,
    EvalReport,
    GoldenTestCase,
    ReActStep,
)
from src.core.ports import IAgentPlanner, IEvalJudge, IToolSandbox


class RunAgentWithEvalUseCase:
    """
    Orquestador convergente (Proyecto 4 + Proyecto 5):
    1. Ejecuta el bucle autónomo ReAct (Thought -> Action -> Observation) dentro del Sandbox con límite de pasos.
    2. Audita inmediatamente la trayectoria con el Juez Evaluador (Evals) antes de certificar la salida.
    """

    def __init__(
        self,
        sandbox: IToolSandbox,
        planner: IAgentPlanner,
        judge: IEvalJudge,
        max_steps: int = 5,
    ) -> None:
        self.sandbox = sandbox
        self.planner = planner
        self.judge = judge
        self.max_steps = max_steps

    def execute(
        self,
        task_prompt: str,
        golden_case: Optional[GoldenTestCase] = None,
    ) -> EvalReport:
        t0 = time.perf_counter()
        tools = self.sandbox.list_available_tools()
        steps: List[ReActStep] = []
        stop_reason = AgentStopReason.MAX_STEPS_REACHED

        for _ in range(self.max_steps):
            s0 = time.perf_counter()
            next_step = self.planner.decide_next_step(
                task_prompt=task_prompt,
                previous_steps=steps,
                available_tools=tools,
            )

            if not next_step.action_tool:
                next_step.latency_ms = round((time.perf_counter() - s0) * 1000, 2)
                steps.append(next_step)
                stop_reason = AgentStopReason.COMPLETED
                break

            observation = self.sandbox.execute_tool(
                tool_name=next_step.action_tool,
                arguments=next_step.action_input,
            )
            next_step.observation = observation
            next_step.latency_ms = round((time.perf_counter() - s0) * 1000, 2)
            steps.append(next_step)

            if "ALERTA DE CUMPLIMIENTO (BLOCKED)" in observation:
                stop_reason = AgentStopReason.GUARDRAIL_BLOCKED
                break

        final_answer = self.planner.synthesize_final_answer(
            task_prompt=task_prompt, steps=steps
        )
        total_ms = round((time.perf_counter() - t0) * 1000, 2)

        # Estimar tokens y costo ($0.15 / 1M tokens equivalente en Gemini Flash)
        total_chars = len(task_prompt) + len(final_answer) + sum(
            len(s.thought) + len(s.observation or "") for s in steps
        )
        est_tokens = max(50, total_chars // 4)
        est_cost = round((est_tokens / 1_000_000) * 0.15, 6)

        trajectory = AgentTrajectory(
            task_prompt=task_prompt,
            steps=steps,
            final_answer=final_answer,
            stop_reason=stop_reason,
            total_latency_ms=total_ms,
            estimated_tokens=est_tokens,
            estimated_cost_usd=est_cost,
        )

        return self.judge.evaluate_trajectory(
            trajectory=trajectory, golden_case=golden_case
        )
