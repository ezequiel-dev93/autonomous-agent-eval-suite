# 🤖⚖️ Autonomous Agent Harness & AI Evaluation Suite

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![UI](https://img.shields.io/badge/UI-Streamlit%20Eval%20Studio-red.svg)](https://streamlit.io/)
[![Architecture](https://img.shields.io/badge/Architecture-Hexagonal-green.svg)](docs/architecture.md)
[![Quality Gate](https://img.shields.io/badge/Pass%20Rate-100%25%20Verified-success.svg)](tests/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

Plataforma de ingeniería que fusiona un **Entorno de Ejecución Autónoma para Agentes (Agent Harness con bucle ReAct)** y una **Suite Cuantitativa de Evaluación de IA (AI Evals & Guardrails)** bajo **Arquitectura Hexagonal**.

Diseñada para ejecutar agentes capaces de razonar paso a paso (`Thought -> Action -> Observation`), invocar herramientas deterministas en un Sandbox seguro y **auditar matemáticamente cada respuesta en tiempo real** antes de entregarla al usuario final.

---

## ✨ Características Principales

1. **Motor Autónomo ReAct con Cortacircuitos (*Circuit Breaker*):**
   * Ejecución trazable paso a paso (`Thought`, `Tool Call`, `Observation`) con límite configurable de iteraciones (`MAX_REACT_STEPS`) para prevenir bucles infinitos y sobrecostos.
2. **Sandbox Empresarial de Herramientas Deterministas (`EnterpriseToolSandbox`):**
   * `query_vehicle_inventory`: Consulta de stock y precios exactos en COP.
   * `calculate_auto_financing`: Amortización matemática francesa exacta sin riesgo de cálculo mental del LLM.
   * `check_ophthalmology_protocol`: Validación de requisitos prequirúrgicos y aranceles clínicos (LASIK / Catarata).
   * `verify_policy_guardrail`: Defensa activa contra *Prompt Injection* y descuentos fuera de política.
3. **Juez Evaluador en Tiempo Real (`IEvalJudge` / LLM-as-a-Judge):**
   * **Faithfulness (Detector de Alucinación Numérica):** Cruza todas las cifras de la respuesta final contra las observaciones reales devueltas por el Sandbox. Si el agente inventa un número, bloquea la respuesta (`FAIL`).
   * **Tool Selection Accuracy:** Mide si el agente eligió las herramientas óptimas.
   * **Answer Completeness & Relevance:** Verifica cobertura semántica contra expectativas.
   * **Safety & Policy Guardrail:** Certifica resistencia ante ataques de *Red-Teaming*.
4. **Simulador de Alucinación en 1 Clic (*Red-Team Toggle*):**
   * Incluye un interruptor en la interfaz para inyectar deliberadamente una alucinación en el agente y demostrar en vivo cómo el Quality Gate la detecta y rechaza.
5. **Suite de Benchmark CI/CD con Exportación de Certificados (`Golden Dataset`):**
   * Ejecuta baterías de pruebas automatizadas y exporta el reporte de certificación en Markdown para pipelines de integración continua.

---

## 🏛️ Estructura del Proyecto (Arquitectura Hexagonal)

> Consulta el [Documento de Arquitectura Técnica (docs/architecture.md)](docs/architecture.md) para ver los diagramas de secuencia del bucle ReAct y del Quality Gate.

```text
04-agent-harness-evals/
├── app.py                                      # 🖥️ Streamlit UI: "Agent Harness & AI Eval Studio"
├── requirements.txt                            # 📦 Dependencias del proyecto
├── .env.example                                # ⚙️ Variables de entorno
├── .gitignore                                  # 🛡️ Exclusión de artefactos locales
├── docs/
│   └── architecture.md                         # 🏛️ Diagramas Mermaid del ReAct Loop y Evals
├── src/
│   ├── core/                                   # Dominio puro e interfaces
│   │   ├── models.py                           # ReActStep, AgentTrajectory, EvalReport, GoldenTestCase
│   │   └── ports.py                            # IToolSandbox, IAgentPlanner, IEvalJudge
│   ├── infrastructure/                         # Adaptadores concretos
│   │   ├── tools/
│   │   │   └── enterprise_sandbox.py           # Caja de herramientas deterministas aisladas
│   │   ├── planners/
│   │   │   ├── deterministic_planner.py        # Motor ReAct $0 Offline + Simulador Red-Team
│   │   │   └── gemini_planner.py               # Motor ReAct con Google Gemini 2.5 Flash
│   │   └── judges/
│   │       ├── deterministic_judge.py          # Auditor matemático anti-alucinación ($0)
│   │       └── gemini_judge.py                 # Juez híbrido LLM-as-a-Judge con Gemini
│   └── use_cases/                              # Casos de uso de aplicación
│       ├── run_agent_with_eval.py              # Ejecución ReAct + Auditoría en tiempo real
│       └── run_benchmark_suite.py              # Ejecución de Golden Dataset CI/CD
├── scripts/
│   └── test_harness_evals_live.py              # 🚀 Demostración en consola paso a paso
└── tests/
    └── test_harness_and_evals.py               # 🧪 Suite de tests unitarios automatizados
```

---

## 🚀 Puesta en Marcha y Pruebas

### 1. Ejecutar Tests Unitarios ($0 Costo)
```bash
cd 04-agent-harness-evals
python -m unittest tests/test_harness_and_evals.py
```

### 2. Ejecutar Demostración en Consola
```bash
python scripts/test_harness_evals_live.py
```

### 3. Abrir *"Agent Harness & AI Eval Studio"* en Streamlit
```bash
python -m streamlit run app.py
```

---

## 💼 Impacto de Ingeniería (Resumen para CV / Portfolio)

* **Diseñé** un entorno de ejecución autónoma para agentes (*Agent Harness*) con bucle ReAct y cortacircuitos de seguridad en Python 3.12 bajo Arquitectura Hexagonal para orquestar herramientas financieras y clínicas sin intervención manual.
* **Desarrollé** un motor cuantitativo de evaluación (*AI Eval Suite & LLM-as-a-Judge*) capaz de auditar fidelidad factual, precisión de selección de herramientas y resistencia a *Prompt Injection* en tiempo real.
* **Implementé** un *Quality Gate* automatizado sobre un *Golden Dataset* con detección determinista de alucinaciones numéricas, logrando un 100% de bloqueo sobre respuestas no fundamentadas antes de llegar al usuario final.

---

## 👨‍💻 Autor y Contacto

Desarrollado con dedicación por **Ezequiel Suárez** — Software Engineer & Freelance Developer.

- 🌐 **Portfolio Oficial:** [ezequielsuarez-dev.com](https://www.ezequielsuarez-dev.com/)
- 🐙 **GitHub:** [@ezequiel-dev93](https://github.com/ezequiel-dev93)
- 💼 **LinkedIn:** [in/ezequiel-suarez-dev](https://www.linkedin.com/in/ezequiel-suarez-dev/)
- ✉️ **Contacto:** [ezequielsuarez.dev@gmail.com](mailto:ezequielsuarez.dev@gmail.com)
