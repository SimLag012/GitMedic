# Setup Guide: Configuration

To operate the **GitMedic Agent** on Windows or Linux, appropriate configuration is required. You no longer need to manually edit any files. 

### First-Time Interactive Wizard
The very first time you execute the `gitmedic` command in your terminal, an interactive setup wizard will launch. It will prompt you for the following variables:

### 1. GitHub Personal Access Token (Classic)
*   **Purpose**: Utilized by the agent to search for issues, clone repositories, and automatically create Pull Requests under your identity.
*   **Detailed Acquisition Steps**:
    1.  Navigate to [GitHub Settings > Developer Settings > Tokens (Classic)](https://github.com/settings/tokens).
    2.  Click **Generate new token** > **Generate new token (classic)**.
    3.  Enter a "Note" to identify the token (e.g., `GitMedic-Agent`).
    4.  Set an **Expiration** (Recommended: 30-90 days).
    5.  **Critically, select the following Scopes**:
        -   `[x] repo` (Full control of private and public repositories). This is mandatory for the agent to commit and push fixes.
        -   `[x] workflow` (Optional, but recommended for projects with GitHub Actions).
    6.  Click **Generate token** and **COPY** the token immediately (you won't be able to see it again!).

### 2. LLM Provider (Ollama / Gemini)
*   **Purpose**: Acts as the core reasoning engine. It analyzes bug descriptions, formulates resolution plans, and generates the necessary code patches.
*   **Acquisition**: If using Gemini, obtain an API key from [Google AI Studio](https://aistudio.google.com/app/apikey). If using Ollama, ensure your local Ollama server is running.

### 3. Operator Wallet Private Key (Optional)
*   **Purpose**: Required for registering the agent's identity via the ERC-8004 standard on the blockchain.
*   **Note**: It is strongly advised to use a dedicated test wallet (e.g., on the Sepolia network). You will be explicitly asked if you wish to configure blockchain settings during the wizard.

### 4. RPC URL (Optional)
*   **Purpose**: Enables the agent to communicate with the Ethereum network to submit the identity registration transaction if blockchain is enabled.

---

### Global Storage
Once completed, your configuration will be saved globally in your home directory at `~/.gitmedic/.env`. GitMedic can then be executed from any folder on your system without requiring local configuration files.
