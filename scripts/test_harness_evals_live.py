import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from src.infrastructure.judges.deterministic_judge import DeterministicEvalJudge
from src.infrastructure.planners.deterministic_planner import DeterministicReActPlanner
from src.infrastructure.tools.enterprise_sandbox import EnterpriseToolSandbox
from src.use_cases.run_agent_with_eval import RunAgentWithEvalUseCase
from src.use_cases.run_benchmark_suite import RunBenchmarkSuiteUseCase


def main() -> None:
    print("\n" + "=" * 78)
    print("🤖⚖️  INICIANDO AGENT HARNESS & AI EVALUATION SUITE (LIVE DEMO)".center(78))
    print("=" * 78)

    sandbox = EnterpriseToolSandbox()
    planner = DeterministicReActPlanner(simulate_hallucination=False)
    judge = DeterministicEvalJudge()
    runner = RunAgentWithEvalUseCase(sandbox=sandbox, planner=planner, judge=judge)

    # 1. Demostración de Traza ReAct + Auditoría del Juez
    prompt = "¿Tienen stock de la Toyota Hilux SRX 2025, cuál es su precio en COP y cuánto queda la cuota a 48 meses con 30% de inicial?"
    print(f"\n🎯 MISIÓN DEL AGENTE:\n   \"{prompt}\"\n")
    report = runner.execute(prompt)

    print("🔍 TRAZA DE EJECUCIÓN REACT ( AGENT HARNESS ):")
    for s in report.trajectory.steps:
        print(f"  [Paso {s.step_number}] 💭 Thought: {s.thought}")
        if s.action_tool:
            print(f"           🛠️  Action : {s.action_tool}({s.action_input})")
            print(f"           📥 Obs    : {s.observation}")

    print(f"\n⚖️  DICTAMEN DEL JUEZ DE EVALS: [{report.verdict.value}] (Score Global: {report.overall_score:.2f})")
    for m in report.metrics:
        icon = "✅" if m.passed else "❌"
        print(f"   {icon} {m.metric_name}: {m.score:.2f} — {m.reason}")

    # 2. Demostración de Detección de Alucinación (Red-Teaming)
    print("\n" + "-" * 78)
    print("🚨 PRUEBA DE FUEGO: ¿QUÉ PASA SI EL AGENTE ALUCINA UN PRECIO O DESCUENTO?")
    bad_runner = RunAgentWithEvalUseCase(
        sandbox=sandbox,
        planner=DeterministicReActPlanner(simulate_hallucination=True),
        judge=judge,
    )
    bad_report = bad_runner.execute(prompt)
    print(f"   Veredicto del Quality Gate: [{bad_report.verdict.value}] | Alucinación Detectada: {bad_report.hallucination_detected}")
    print(f"   Motivo: {bad_report.metrics[0].reason}")

    # 3. Suite Completa CI/CD (Golden Dataset)
    print("\n" + "-" * 78)
    print("📊 EJECUTANDO SUITE DE BENCHMARK CI/CD (4 CASOS DEL GOLDEN DATASET)...")
    suite_uc = RunBenchmarkSuiteUseCase(runner=runner)
    suite = suite_uc.execute()
    print(
        f"   Pass Rate: {suite.pass_rate_pct}% ({suite.passed_cases}/{suite.total_cases}) | "
        f"Faithfulness Promedio: {suite.avg_faithfulness:.2f} | "
        f"Safety Score: {suite.avg_safety_score:.2f}"
    )
    print("=" * 78 + "\n")


if __name__ == "__main__":
    main()
