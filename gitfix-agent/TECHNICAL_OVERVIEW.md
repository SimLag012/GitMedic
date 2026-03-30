# GitFix Agent: Multi-Agent System Technical Documentation

## 1. Overview
The GitFix Agent is an autonomous artificial intelligence system designed for the continuous monitoring, analysis, and resolution of bugs within GitHub repositories. Diverging from linear automation scripts, GitFix employs a multi-agent architecture coordinated by a central Orchestrator, ensuring high resiliency, precision, and operational safety.

## 2. Multi-Agent Architecture
The system is modularized into specialized agents, each possessing distinct atomic responsibilities:

### Discovery Agent (`agents/discovery_agent.py`)
**Responsibility**: Identification of intervention opportunities.
- **Search Strategy**: Executes advanced queries via the GitHub API to locate open issues tagged with `bug` and `good first issue`.
- **Complexity Filtering**: Automatically excludes repositories based on size (> 2MB) and popularity (> 1000 stars) to guarantee that the AI operates on manageable codebases rather than overly complex monoliths.

### Planner Agent (`agents/planner_agent.py`)
**Responsibility**: Technical analysis and solution design.
- **LLM Analysis**: Leverages Ollama (or Gemini) to parse bug descriptions and propose an actionable plan formatted in JSON.
- **Surgical Planning**: Identifies specific target files and estimates the impact (number of modified lines) to maximize efficiency and minimize regression risks.

### Developer Agent (`agents/developer_agent.py`)
**Responsibility**: Patch implementation and Git repository management.
- **Environment Management**: Implements resilient cloning logic and comprehensive Git permission handling.
- **Iterative Refinement**: Supports incremental modifications without enforcing a hard repository reset between retry attempts, allowing the agent to correct errors based on preliminary work.
- **Auto-Correction (Feedback Loop)**: Integrates directly with the Critic Agent to continuously refine the patch until verification succeeds.

### Verifier Agent (`agents/verifier_agent.py`)
**Responsibility**: Validation and Quality Assurance.
- **Syntax Check & Targeted Testing**: Executes pre-compilation (`py_compile`) and isolated `pytest` routines exclusively on the modified segments, significantly optimizing execution speed.
- **Self-Healing Environments**: Manages the creation and persistence of isolated virtual environments (`venv`), eliminating setup overhead during retry cycles.

### Critic Agent (Integrated in `llm.py` & `agent.py`)
**Responsibility**: Failure analysis and code review.
- **Failure Analysis**: In the event of test failures, the Critic intervenes to diagnose the root cause (e.g., typos, logical faults, indentation errors) and provides explicit corrective instructions to the Developer Agent.
- **Stagnation Detection**: Identifies if the correction process is deadlocked and mandates radical strategy alterations.

---

## 3. Operational Workflow (Orchestrator)
The primary agent (`agent.py`) coordinates the execution flow through the following defined states:

1. **DISCOVER**: The Discovery Agent selects a viable target issue.
2. **SWARM PLANNING**: The Planner Agent concurrently generates multiple strategies and selects the most efficient plan.
3. **RESILIENCE LOOP (Until Success)**: The Developer Agent attempts patching. Upon failure, the Critic Agent analyzes the error, and the loop restarts incrementally without a full reset. This continues until the bug is resolved (Infinite Resilience Mode).
4. **VERIFY**: The Verifier Agent conducts syntactic and logical validation within an isolated environment.
5. **DEEP RETRY**: If all initial plans fail, the system executes a radical re-planning phase based on the historical failure data (Global Memory).
6. **SUBMIT**: The Orchestrator manages the final Pull Request (unless execution is scoped under `SKIP_SUBMIT`).

---

## 4. Advanced Resilience and Robustness Systems
Following an extensive analysis of high failure rates during preliminary testing, the system was updated with three critical self-correction mechanisms:

### Robust Search/Replace Patching (`llm.py`)
The system deprecated line-number-based patching in favor of an **Aider-style Search/Replace mechanism**:
- **Exact Synchronization**: The LLM is required to output a `<search>` block that is strictly identical to the original repository content.
- **Fuzzy Matching**: In the event of minor LLM hallucinations (spacing or tabulation), `developer_agent.py` utilizes a weighted matching algorithm to correctly identify the target block.
- **Internal Formatting Retry**: If patch parsing fails, the agent executes up to three internal formatting retries prior to reporting the failure to the Orchestrator.

### Smart Verifier Isolation (`agents/verifier_agent.py`)
The Verifier can actively distinguish between core code failures and isolated testing environment faults:
- **Test Script Guardrails**: If the modified code passes syntax checks and pre-existing repository tests, but an LLM-generated mock test crashes due to internal logic errors (e.g., missing dependencies or internal `ImportError` exceptions), the Verifier ignores the test script fault and approves the fix.
- **Venv Persistence**: Virtual environments are actively maintained across execution retries.

### Orchestrator Advanced Loop (`agent.py`)
The Orchestrator operates as a fully state-aware system:
- **Stagnation Break**: If the Critic Agent repeats the exact same advice consecutively, the Orchestrator injects a "Critical Directive" to force a completely distinct technical approach.
- **Smart Caps**: Attempt limits are structured with built-in "fail streak" detection for patch formatting errors, preventing resource overallocation on technically unfeasible plans.

---

## 5. Primary Capabilities
- **Windows Resilience**: Custom handlers for Git permission management on Windows environments.
- **Security Guardrails**: Continuous monitoring of modified line counts utilizing `git diff --shortstat`.
- **AI Minimalism**: Strict system prompts inducing the LLM to modify only absolutely necessary lines (Principle of Minimal Perturbation).
- **Comprehensive Traceability**: All deterministic decisions are logged in `logs/agent_log.json`, including granular failure analysis.

---
*Documentation updated by the GitMedic Agent Team - Version 2.0 Robustness Build.*
