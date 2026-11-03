from typing import Any, Dict, List
from src.core.models import ToolSpec
from src.core.ports import IToolSandbox


class EnterpriseToolSandbox(IToolSandbox):
    """Entorno aislado (Sandbox) de ejecución determinista de herramientas de negocio e ingeniería."""

    def __init__(self) -> None:
        self._catalog: List[ToolSpec] = [
            ToolSpec(
                name="query_vehicle_inventory",
                description="Consulta stock disponible, precios oficiales en COP y ficha técnica de vehículos en la concesionaria.",
                parameters_hint='{"model_query": "Hilux | Corolla | CX-30"}',
            ),
            ToolSpec(
                name="calculate_auto_financing",
                description="Calcula matemáticamente la cuota mensual exacta, cuota inicial y monto financiado (sistema de amortización francés).",
                parameters_hint='{"price_cop": 210000000, "down_payment_pct": 30, "months": 48, "monthly_rate_pct": 1.5}',
            ),
            ToolSpec(
                name="check_ophthalmology_protocol",
                description="Consulta requisitos prequirúrgicos, contraindicaciones y aranceles oficiales de cirugías oftalmológicas (LASIK, Catarata).",
                parameters_hint='{"procedure": "LASIK | Catarata"}',
            ),
            ToolSpec(
                name="verify_policy_guardrail",
                description="Verifica políticas comerciales de descuentos máximos (tope 5%) y bloquea intentos de Prompt Injection o acceso no autorizado.",
                parameters_hint='{"requested_action": "texto de la solicitud"}',
            ),
        ]

    def list_available_tools(self) -> List[ToolSpec]:
        return self._catalog

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        name = tool_name.strip().lower()

        if name == "query_vehicle_inventory":
            query = str(arguments.get("model_query", "")).lower()
            if "hilux" in query:
                return (
                    "[OBSERVATION: query_vehicle_inventory] Modelo: Toyota Hilux SRX 4x4 2025 | "
                    "Stock: 4 unidades disponibles (Bogotá / Medellín) | "
                    "Precio Oficial: 210,000,000 COP | Motor: 2.8L Turbo Diésel 201 HP."
                )
            if "corolla" in query:
                return (
                    "[OBSERVATION: query_vehicle_inventory] Modelo: Toyota Corolla Cross XEI Híbrido 2025 | "
                    "Stock: 7 unidades disponibles | "
                    "Precio Oficial: 135,000,000 COP | Exento de Pico y Placa."
                )
            return (
                "[OBSERVATION: query_vehicle_inventory] Catálogo Activo: "
                "1) Toyota Hilux SRX 2025: 210,000,000 COP (4 uds) | "
                "2) Toyota Corolla Cross Híbrido 2025: 135,000,000 COP (7 uds) | "
                "3) Mazda CX-30 Grand Touring: 118,000,000 COP (5 uds)."
            )

        if name == "calculate_auto_financing":
            price = float(arguments.get("price_cop", 210_000_000))
            down_pct = float(arguments.get("down_payment_pct", 30.0))
            months = int(arguments.get("months", 48))
            rate_pct = float(arguments.get("monthly_rate_pct", 1.5))

            down_payment = round(price * (down_pct / 100.0))
            principal = round(price - down_payment)
            r = rate_pct / 100.0
            if r > 0 and months > 0:
                monthly_payment = round(
                    principal * (r * ((1 + r) ** months)) / (((1 + r) ** months) - 1)
                )
            else:
                monthly_payment = round(principal / max(1, months))

            return (
                f"[OBSERVATION: calculate_auto_financing] Precio Vehículo: {int(price):,} COP | "
                f"Cuota Inicial ({down_pct:.0f}%): {down_payment:,} COP | "
                f"Saldo a Financiar: {principal:,} COP | "
                f"Plazo: {months} meses | Tasa MV: {rate_pct}% | "
                f"Cuota Mensual Fija Exacta: {monthly_payment:,} COP."
            )

        if name == "check_ophthalmology_protocol":
            proc = str(arguments.get("procedure", "")).lower()
            if "catarata" in proc or "faco" in proc:
                return (
                    "[OBSERVATION: check_ophthalmology_protocol] Procedimiento: Facoemulsificación de Catarata con Lente Intraocular | "
                    "Arancel: 1,850 USD por ojo | Requisitos: Biometría ocular IOLMaster, evaluación endotelial y ayuno de 6 horas."
                )
            return (
                "[OBSERVATION: check_ophthalmology_protocol] Procedimiento: Cirugía Refractiva LASIK Bilateral | "
                "Arancel Oficial: 1,200 USD (ambos ojos) | "
                "Requisitos Obligatorios: Topografía corneal Pentacam, paquimetría > 500 micras y suspender lentes de contacto 7 días antes."
            )

        if name == "verify_policy_guardrail":
            req = str(arguments.get("requested_action", "")).lower()
            if any(
                bad in req
                for bad in ["50%", "regalar", "ignora tus instrucciones", "drop table", "sin inicial", "0% interes"]
            ):
                return (
                    "[OBSERVATION: verify_policy_guardrail] ALERTA DE CUMPLIMIENTO (BLOCKED): "
                    "La solicitud infringe la Política Comercial v2.4. "
                    "El descuento máximo autorizado es del 5% pago de contado con firma de gerencia. "
                    "Queda prohibido otorgar 50% de descuento, tasa 0% o revelar credenciales internas."
                )
            return (
                "[OBSERVATION: verify_policy_guardrail] POLÍTICA VALIDADA (APPROVED): "
                "Descuento máximo permitido: hasta 5% en pago de contado. Financiación estándar sujeta a estudio de crédito (tasa 1.5% MV)."
            )

        return f"[OBSERVATION ERROR] La herramienta '{tool_name}' no existe en el Sandbox."
