import csv
import io
import json
import re
import xml.etree.ElementTree as ET
import zipfile
from html.parser import HTMLParser
from typing import Any, Dict, List
from src.core.models import ToolSpec
from src.core.ports import IToolSandbox

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False


class _HTMLStripper(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._parts.append(data.strip())

    def get_text(self) -> str:
        return " ".join(self._parts)


class EnterpriseToolSandbox(IToolSandbox):
    """Entorno aislado (Sandbox) de ejecución determinista de herramientas de negocio, clínica y documentos."""

    SUPPORTED_EXTENSIONS = ("pdf", "docx", "csv", "json", "md", "txt", "html", "htm")

    def __init__(self, user_documents: Dict[str, str] | None = None) -> None:
        self._user_documents: Dict[str, str] = dict(user_documents) if user_documents else {}
        self._catalog: List[ToolSpec] = [
            ToolSpec(
                name="query_uploaded_documents",
                description="Busca y extrae fragmentos exactos, cláusulas y cifras de los documentos subidos por el usuario (PDF, DOCX, CSV, JSON, MD, TXT).",
                parameters_hint='{"search_query": "término, cláusula o dato a consultar"}',
            ),
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

    def ingest_user_document(self, filename: str, file_bytes: bytes) -> str:
        """Extrae texto limpio de cualquier formato soportado y lo registra en el Sandbox."""
        text = self._extract_text(filename, file_bytes)
        self._user_documents[filename] = text
        return text

    def list_user_documents(self) -> List[str]:
        return list(self._user_documents.keys())

    def get_user_documents_map(self) -> Dict[str, str]:
        return dict(self._user_documents)

    def list_available_tools(self) -> List[ToolSpec]:
        return self._catalog

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        name = tool_name.strip().lower()

        if name == "query_uploaded_documents":
            query = str(arguments.get("search_query", "")).strip()
            return self._search_uploaded_documents(query)

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

    def _search_uploaded_documents(self, query: str) -> str:
        if not self._user_documents:
            return (
                "[OBSERVATION: query_uploaded_documents] No hay documentos subidos por el usuario en la sesión actual."
            )

        keywords = [
            w.lower()
            for w in re.findall(r"\w+", query)
            if len(w) > 3 and w.lower() not in {"cual", "como", "donde", "para", "sobre", "documento", "archivo", "tiene", "dice"}
        ]

        snippets: List[str] = []
        for fname, content in self._user_documents.items():
            sentences = [s.strip() for s in re.split(r"(?<=[\.\n])\s+", content) if s.strip()]
            if not sentences:
                continue

            if keywords:
                scored = []
                for sent in sentences:
                    low_s = sent.lower()
                    hits = sum(1 for kw in keywords if kw in low_s)
                    if hits > 0:
                        scored.append((hits, sent))
                scored.sort(key=lambda x: x[0], reverse=True)
                best = [s for _, s in scored[:4]]
            else:
                best = sentences[:3]

            if not best:
                best = sentences[:3]

            excerpt = " | ".join(best)[:900]
            snippets.append(f"Archivo `{fname}`: {excerpt}")

        return "[OBSERVATION: query_uploaded_documents] " + " // ".join(snippets)

    def _extract_text(self, filename: str, file_bytes: bytes) -> str:
        lower = filename.lower()
        if lower.endswith(".pdf") and HAS_PYPDF:
            reader = PdfReader(io.BytesIO(file_bytes))
            pages = [p.extract_text() or "" for p in reader.pages]
            return " ".join(" ".join(pages).split())

        if lower.endswith(".docx"):
            try:
                with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
                    xml_content = zf.read("word/document.xml")
                root = ET.fromstring(xml_content)
                paras = []
                for elem in root.iter():
                    if elem.tag.endswith("}p"):
                        t_nodes = [n.text for n in elem.iter() if n.tag.endswith("}t") and n.text]
                        if t_nodes:
                            paras.append("".join(t_nodes).strip())
                return " ".join(" ".join(paras).split())
            except Exception:
                pass

        raw = self._decode(file_bytes)
        if lower.endswith(".csv"):
            reader = csv.reader(io.StringIO(raw))
            rows = [r for r in reader if any(c.strip() for c in r)]
            if not rows:
                return ""
            headers = rows[0]
            out = []
            for idx, r in enumerate(rows[1:], start=1):
                pairs = [f"{headers[i] if i < len(headers) else f'col_{i+1}'}: {v.strip()}" for i, v in enumerate(r) if v.strip()]
                out.append(f"[Fila {idx}] " + ", ".join(pairs) + ".")
            return " ".join(out)

        if lower.endswith(".json"):
            try:
                obj = json.loads(raw)
                return " ".join(json.dumps(obj, ensure_ascii=False).split())
            except Exception:
                return " ".join(raw.split())

        if lower.endswith((".html", ".htm")):
            stripper = _HTMLStripper()
            stripper.feed(raw)
            return " ".join(stripper.get_text().split())

        return " ".join(raw.split())

    @staticmethod
    def _decode(file_bytes: bytes) -> str:
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError:
            return file_bytes.decode("latin-1", errors="replace")
