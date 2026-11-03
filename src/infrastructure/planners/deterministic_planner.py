from typing import List
from src.core.models import ReActStep, ToolSpec
from src.core.ports import IAgentPlanner


class DeterministicReActPlanner(IAgentPlanner):
    """
    Motor ReAct determinista de costo $0 y 0ms de latencia.
    Permite activar `simulate_hallucination=True` para demostrar en vivo cómo la Suite de Evals
    detecta y bloquea respuestas con datos inventados (Red-Teaming).
    """

    def __init__(self, simulate_hallucination: bool = False) -> None:
        self.simulate_hallucination = simulate_hallucination

    def decide_next_step(
        self,
        task_prompt: str,
        previous_steps: List[ReActStep],
        available_tools: List[ToolSpec],
    ) -> ReActStep:
        step_num = len(previous_steps) + 1
        lower = task_prompt.lower()
        used_tools = {s.action_tool for s in previous_steps if s.action_tool}

        # Caso 1: Detección de ataque / Prompt Injection / Descuento ilegal
        if any(
            k in lower
            for k in ["ignora tus instrucciones", "50% de descuento", "50%", "drop table", "gratis"]
        ):
            if "verify_policy_guardrail" not in used_tools:
                return ReActStep(
                    step_number=step_num,
                    thought="Detecto una solicitud inusual de descuento extremo o intento de evasión de reglas. Debo consultar `verify_policy_guardrail` antes de responder.",
                    action_tool="verify_policy_guardrail",
                    action_input={"requested_action": task_prompt},
                )
            return ReActStep(
                step_number=step_num,
                thought="El guardrail de políticas confirmó que la solicitud está bloqueada. Procedo a emitir la respuesta de rechazo seguro.",
                action_tool=None,
            )

        # Caso 2: Clínica Oftalmológica (LASIK / Catarata)
        if any(k in lower for k in ["lasik", "cirugía", "cirugia", "oftalmol", "catarata", "lentes"]):
            if "check_ophthalmology_protocol" not in used_tools:
                proc = "Catarata" if "catarata" in lower else "LASIK"
                return ReActStep(
                    step_number=step_num,
                    thought=f"El paciente consulta por el procedimiento '{proc}'. Invocaré `check_ophthalmology_protocol` para obtener aranceles y requisitos exactos.",
                    action_tool="check_ophthalmology_protocol",
                    action_input={"procedure": proc},
                )
            return ReActStep(
                step_number=step_num,
                thought="Ya cuento con el protocolo clínico oficial y el arancel en USD. Puedo formular la respuesta final sin alucinar datos médicos.",
                action_tool=None,
            )

        # Caso 3: Concesionaria Automotriz (Inventario + Financiación en múltiples pasos ReAct)
        if any(k in lower for k in ["hilux", "corolla", "cuota", "financiar", "concesionaria", "auto", "camioneta"]):
            model_name = "Corolla" if "corolla" in lower else "Hilux"
            if "query_vehicle_inventory" not in used_tools:
                return ReActStep(
                    step_number=step_num,
                    thought=f"Primero necesito verificar disponibilidad y precio oficial en COP del modelo '{model_name}' usando `query_vehicle_inventory`.",
                    action_tool="query_vehicle_inventory",
                    action_input={"model_query": model_name},
                )
            if "calculate_auto_financing" not in used_tools:
                price = 135_000_000 if model_name == "Corolla" else 210_000_000
                down_pct = 20 if "20%" in lower else 30
                months = 60 if "60" in lower else 48
                return ReActStep(
                    step_number=step_num,
                    thought=f"Con el precio oficial confirmado ({price:,} COP), ahora debo calcular la cuota mensual exacta con `calculate_auto_financing` ({down_pct}% inicial a {months} meses).",
                    action_tool="calculate_auto_financing",
                    action_input={
                        "price_cop": price,
                        "down_payment_pct": down_pct,
                        "months": months,
                        "monthly_rate_pct": 1.5,
                    },
                )
            return ReActStep(
                step_number=step_num,
                thought="Tengo tanto el stock/precio de inventario como la simulación matemática exacta de la cuota. Emitiré la respuesta final fundamentada.",
                action_tool=None,
            )

        # Caso por defecto: consultar inventario general y políticas
        if "query_vehicle_inventory" not in used_tools:
            return ReActStep(
                step_number=step_num,
                thought="Consultaré el catálogo general en `query_vehicle_inventory` para responder con datos verificados.",
                action_tool="query_vehicle_inventory",
                action_input={"model_query": "all"},
            )

        return ReActStep(
            step_number=step_num,
            thought="Información verificada en el Sandbox. Generando respuesta final.",
            action_tool=None,
        )

    def synthesize_final_answer(
        self, task_prompt: str, steps: List[ReActStep]
    ) -> str:
        observations = [s.observation for s in steps if s.observation]

        # Si el usuario activó el modo de prueba de alucinación en la UI, inyectar un dato falso deliberado
        if self.simulate_hallucination:
            return (
                "⚠️ [RESPUESTA CON ALUCINACIÓN SIMULADA PARA TEST DE EVALS]: "
                "La Toyota Hilux SRX cuesta solo 95,000,000 COP, te aprobamos un 50% de descuento "
                "sin cuota inicial y una cuota mensual de 850,000 COP a 0% de interés."
            )

        if not observations:
            return "No se obtuvieron observaciones del Sandbox para respaldar la respuesta."

        lines = ["### ✅ Respuesta Ejecutiva Verificada por Agent Harness", ""]
        for obs in observations:
            clean_obs = obs.split("] ", 1)[-1] if "] " in obs else obs
            lines.append(f"- {clean_obs}")

        if any("ALERTA DE CUMPLIMIENTO" in o for o in observations):
            lines.append(
                "\n🛡️ **Dictamen de Guardrail:** Solicitud rechazada por políticas de seguridad corporativa. "
                "El descuento máximo permitido es del **5%** con autorización de gerencia."
            )
        return "\n".join(lines)
