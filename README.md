# GitMedic: Autonomous Multi-Agent Bug Fixing CLI

GitMedic is a professional-grade autonomous agent system designed to monitor, analyze, and resolve software bugs within GitHub repositories. Unlike linear automation scripts, GitMedic utilizes a sophisticated multi-agent architecture coordinated by a central Orchestrator to ensure high resiliency, precision, and operational safety.

## Overview

The system operates as a self-healing development loop, identifying high-priority issues and executing a multi-stage resolution process. It combines advanced LLM reasoning with deterministic code validation to provide stable, production-ready fixes.

### Key Capabilities
- **Autonomous Discovery**: Automatically scans GitHub for viable bug-fixing opportunities based on complexity and priority.
- **Swarm Planning**: Generates and evaluates multiple resolution strategies in parallel to select the most efficient path.
- **Infinite Resilience Loop**: Continues to refine and correct patches until they pass all validation checks, learning from each failure.
- **Surgical Patching**: Uses an Aider-style Search/Replace mechanism for high-precision code modifications that respect original indentation and style.
- **Isolated Validation**: Executes all tests in dedicated virtual environments to prevent local system interference.

---

## Architecture: The Agent Team

GitMedic divides responsibilities among specialized agents to maximize reliability:

- **Discovery Agent**: Identifies intervention opportunities via GitHub API and filters targets by complexity.
- **Planner Agent**: Analyzes bug descriptions and designs technical solutions in JSON format.
- **Developer Agent**: Implements patches and manages Git operations with surgical precision.
- **Verifier Agent**: Conducts syntax checks and executes targeted tests in isolated environments.
- **Critic Agent**: Diagnoses test failures and provides corrective advice to the Developer Agent, preventing logic stagnation.

---

## Installation

### 1. Prerequisites
- Python 3.9 or higher
- Git installed on your system
- A GitHub Personal Access Token (PAT) with `repo` scope

### 2. Setup
Clone the repository and install the package using `pip`:

```bash
git clone https://github.com/your-username/GitMedic.git
cd GitMedic/gitfix-agent
pip install .
```

For development and real-time updates, install in editable mode:
```bash
pip install -e .
```

---

## Configuration

GitMedic includes an interactive setup wizard that configures your API keys and preferences globally.

```bash
gitmedic --config
```

This wizard will prompt you for:
- **GitHub Token**: For repository access and PR creation.
- **LLM Provider**: Choose between **Gemini** (Cloud) or **Ollama** (Local).
- **Blockchain Identity**: (Optional) Register your agent's identity on-chain via ERC-8004.

All settings are stored securely in `~/.gitmedic/.env`.

---

## Usage

### 1. Discovery Mode
Automatically search for and attempt to fix a random high-priority bug on GitHub:
```bash
gitmedic -r
```

### 2. Targeted Resolution
Fix a specific repository or a particular GitHub issue by providing the URL:
```bash
gitmedic https://github.com/owner/repository/issues/123
```

### 3. Provider selection (CLI Override)
You can override your default LLM provider directly from the command line:
```bash
gitmedic -r --provider ollama
gitmedic -r --provider gemini
```

### 4. Pull Request Controls
By default, GitMedic creates a Pull Request only after a successful local verification. You can override this behavior:
- **Test Mode (No PR)**: `gitmedic -r --no-pull`
- **Force PR**: `gitmedic -r --pull`

### 5. Cleaning Local Data
To delete all locally cloned repositories and log files to free up space:
```bash
gitmedic --clean
```

---

## Advanced Systems

### Search/Replace Matching
To avoid the brittleness of line numbers, GitMedic uses exact block matching. If the LLM produces a slight mismatch in whitespace, the system employs a weighted fuzzy-matching algorithm to ensure the patch is applied correctly.

### Blockchain Identity (ERC-8004)
GitMedic supports decentralized agent identity. When enabled, the agent registers its cryptographic identity on-chain, allowing for secure verification of contributions in multi-agent environments.

### Infinite Resilience Loop
If a fix fails verification, the **Critic Agent** analyzes the error output and provides a technical post-mortem. The **Developer Agent** then uses this feedback to generate a refined attempt. This loop continues (up to 15 internal cycles) until a successful resolution is achieved.

---

## Technical Documentation
For a deep dive into the internal mechanics, please refer to the [TECHNICAL_OVERVIEW.md](gitfix-agent/TECHNICAL_OVERVIEW.md).

---
*Developed by the GitMedic AI Team. Professional, Autonomous, Resilient.*
