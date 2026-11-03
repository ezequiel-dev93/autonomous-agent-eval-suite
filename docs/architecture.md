# 🏛️ Especificación de Arquitectura: Agent Harness & AI Evaluation Suite

> Diseño técnico convergente que fusiona un **Entorno de Ejecución Autónoma para Agentes (Agent Harness / ReAct Loop)** con una **Suite Cuantitativa de Evaluación y Guardrails (AI Evals / LLM-as-a-Judge)**.

---

## 📌 1. Por qué convergen el Agent Harness y la Suite de Evals

En sistemas de IA empresariales, ejecutar un agente autónomo sin auditar matemáticamente sus pasos genera riesgo de alucinación financiera o clínica. Al unir ambos motores bajo **Arquitectura Hexagonal**:
1. El **Agent Harness** resuelve tareas complejas paso a paso (`Thought -> Action -> Observation`) dentro de un Sandbox con límite de iteraciones (*Circuit Breaker*).
2. El **Eval Judge** intercepta la traza completa antes de entregar la respuesta al cliente, verificando que cada cifra numérica provenga de una observación real del Sandbox y que no se haya violado ninguna política corporativa.

---

## 🏗️ 2. Diagrama de Arquitectura Hexagonal

```mermaid
flowchart TB
    subgraph Driving["Adaptadores de Entrada (Driving)"]
        UI["Streamlit Studio (app.py)\n- Live ReAct + Real-Time Judge\n- CI/CD Benchmark Suite"]
        CLI["CLI Live Runner & CI/CD Script"]
    end

    subgraph UseCases["Capa de Aplicación (Casos de Uso)"]
        UC1["RunAgentWithEvalUseCase\n(Orquesta Loop ReAct + Auditoría del Juez)"]
        UC2["RunBenchmarkSuiteUseCase\n(Ejecuta Golden Dataset + Reporte CI/CD)"]
    end

    subgraph Domain["Dominio Puro (Core)"]
        Models["Entidades:\nReActStep, AgentTrajectory,\nEvalMetricScore, EvalReport, GoldenTestCase"]
        Ports["Puertos:\nIToolSandbox, IAgentPlanner, IEvalJudge"]
    end

    subgraph Driven["Adaptadores de Infraestructura (Driven)"]
        Sandbox["EnterpriseToolSandbox\n- query_vehicle_inventory\n- calculate_auto_financing\n- check_ophthalmology_protocol\n- verify_policy_guardrail"]
        Planners["Planners ReAct:\n- DeterministicReActPlanner ($0 + Red-Team Toggle)\n- GeminiReActPlanner (gemini-2.5-flash)"]
        Judges["Judges de Evaluación:\n- DeterministicEvalJudge (Anti-Hallucination Math)\n- GeminiEvalJudge (LLM-as-a-Judge)"]
    end

    Driving --> UseCases
    UseCases --> Domain
    Domain -.-> Driven
```

---

## 🔄 3. Flujo de Ejecución Autónoma y Quality Gate

```mermaid
sequenceDiagram
    autonumber
    actor Usuario
    participant Runner as RunAgentWithEvalUseCase
    participant Planner as IAgentPlanner (ReAct)
    participant Sandbox as EnterpriseToolSandbox
    participant Judge as IEvalJudge (Evals)

    Usuario->>Runner: "¿Precio de Hilux SRX y cuota a 48 meses con 30% inicial?"
    loop Bucle ReAct (Máx 5 pasos)
        Runner->>Planner: decide_next_step(prompt, steps)
        Planner-->>Runner: Thought + Action(query_vehicle_inventory / calculate_auto_financing)
        Runner->>Sandbox: execute_tool(tool_name, args)
        Sandbox-->>Runner: Observation determinista (210,000,000 COP | Cuota: 4,318,125 COP)
    end
    Runner->>Planner: synthesize_final_answer(steps)
    Planner-->>Runner: Respuesta consolidada
    Runner->>Judge: evaluate_trajectory(trajectory)
    Judge->>Judge: 1. Verifica números vs Observaciones (Faithfulness)\n2. Evalúa herramientas usadas\n3. Valida Guardrails de seguridad
    Judge-->>Runner: EvalReport (Verdict: PASS | Score: 0.99)
    Runner-->>Usuario: Traza ReAct + Respuesta Certificada + Reporte de Evals
```
