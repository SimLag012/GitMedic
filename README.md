# GitMedic - Autonomous Bug Fixing Agent

GitMedic is an advanced autonomous agent designed to scan GitHub repositories, identify bugs, plan a resolution, test it locally, and (optionally) create a Pull Request to resolve them automatically.

## Installation

To use GitMedic locally, follow these steps:

### 1. Clone the Repository
Download the source code and navigate to the agent directory:
```bash
git clone https://github.com/your-username/GitMedic.git
cd GitMedic/gitfix-agent
```

### 2. Install Dependencies
Ensure Python 3.8+ is installed. Then, run the following command to install the CLI tool:
```bash
pip install .
```
*(For development, use `pip install -e .` to install it in editable mode.)*

### 3. First-Time Setup
GitMedic features an interactive setup wizard. Simply run the command for the first time, and it will prompt you for your configuration credentials (GitHub token and LLM Provider configuration, such as Ollama).

These credentials will be saved globally to `~/.gitmedic/.env`.

```bash
gitmedic -h
```

---

## Usage Examples

GitMedic can be executed from the terminal by running the `gitmedic` command.

**1. Discovery Mode (Search and Fix Random Bugs):**
To instruct the agent to automatically search for high-priority bugs on GitHub and attempt to resolve them:
```bash
gitmedic -r
```

**2. Resolve a Specific Bug:**
To fix a known repository or a specific GitHub issue, provide the target URL:
```bash
gitmedic https://github.com/organization/project
```

### Pull Request Settings
GitMedic offers flags to strictly control the submission of Pull Requests to the target repository.

- **Skip Pull Request (Test Mode):** To test the agent locally without creating a Pull Request on GitHub, use the `--no-pull` flag:
  ```bash
  gitmedic -r --no-pull
  gitmedic https://github.com/organization/project --no-pull
  ```

- **Force Pull Request:**
  To forcefully create a Pull Request upon successful execution and testing, overriding any internal constraints:
  ```bash
  gitmedic -r --pull
  ```

## Requirements
- Python 3.8+
- GitHub Account and Personal Access Token
- (Optional) Ollama for local LLM inference, or Gemini/OpenAI API access.
