import os
from rich import print as rprint

import pathlib
from dotenv import load_dotenv, set_key

from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

def get_config_dir():
    """Returns the path to the global ~/.gitmedic directory."""
    home = pathlib.Path.home()
    config_dir = home / ".gitmedic"
    if not config_dir.exists():
        config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir

def get_env_path():
    """Returns the path to the global ~/.gitmedic/.env file."""
    return get_config_dir() / ".env"

def run_setup_wizard(env_path):
    """Interactively prompts the user for required configuration variables with validation."""
    console.rprint("\n[bold cyan]=== GitMedic Configuration Wizard ===[/bold cyan]")
    
    # Load existing config if it exists
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)
        console.rprint("Existing configuration found. Press [bold]Enter[/bold] to keep current values.\n")
    else:
        console.rprint("Welcome to GitMedic! Let's configure your agent.\n")
    
    console.rprint("Configuration will be saved to:")
    console.rprint(f"[bold yellow]{env_path}[/bold yellow]\n")

    # Current values
    curr_github_token = os.getenv("GITHUB_TOKEN", "")
    curr_llm_provider = os.getenv("LLM_PROVIDER", "ollama")
    curr_gemini_api_key = os.getenv("GEMINI_API_KEY", "")
    curr_ollama_model = os.getenv("OLLAMA_MODEL", "gpt-oss:120b-cloud")
    curr_private_key = os.getenv("OPERATOR_WALLET_PRIVATE_KEY", "")
    curr_rpc_url = os.getenv("RPC_URL", "")
    curr_skip_blockchain = os.getenv("SKIP_BLOCKCHAIN", "true").lower() == "true"

    # GitHub Token
    github_token = Prompt.ask("[bold green]GitHub Personal Access Token[/bold green]", default=curr_github_token)
    while not github_token.strip():
        console.rprint("[red]Error: GitHub Token is required.[/red]")
        github_token = Prompt.ask("[bold green]GitHub Personal Access Token[/bold green]")

    llm_provider = Prompt.ask("[bold green]LLM Provider[/bold green]", choices=["ollama", "gemini"], default=curr_llm_provider)
    
    gemini_api_key = curr_gemini_api_key
    ollama_model = curr_ollama_model
    
    if llm_provider == "gemini":
        gemini_api_key = Prompt.ask("[bold green]Gemini API Key[/bold green]", default=curr_gemini_api_key)
        while not gemini_api_key.strip():
            console.rprint("[red]Error: Gemini API Key is required for the Gemini provider.[/red]")
            gemini_api_key = Prompt.ask("[bold green]Gemini API Key[/bold green]")
    elif llm_provider == "ollama":
        ollama_model = Prompt.ask("[bold green]Ollama Model[/bold green]", default=curr_ollama_model)

    console.rprint("\n[bold cyan]--- Ethereum Agent Identity (ERC-8004) ---[/bold cyan]")
    console.rprint("GitMedic can register its identity on-chain for secure agent-to-agent verification.")
    
    # default for blockchain is the inverse of SKIP_BLOCKCHAIN
    configure_blockchain = Confirm.ask("Do you want to enable Ethereum identity registration?", default=not curr_skip_blockchain)
    
    private_key = curr_private_key
    rpc_url = curr_rpc_url
    
    if configure_blockchain:
        private_key = Prompt.ask("[bold green]Agent Wallet Private Key[/bold green]", default=curr_private_key)
        while not private_key.strip():
            console.rprint("[red]Error: Private Key is required if blockchain is enabled.[/red]")
            private_key = Prompt.ask("[bold green]Agent Wallet Private Key[/bold green]")
        
        rpc_url = Prompt.ask("[bold green]RPC URL[/bold green]", default=curr_rpc_url)
        while not rpc_url.strip():
            console.rprint("[red]Error: RPC URL is required if blockchain is enabled.[/red]")
            rpc_url = Prompt.ask("[bold green]RPC URL[/bold green]")
    else:
        console.rprint("[yellow]Blockchain registration disabled. (SKIP_BLOCKCHAIN=true)[/yellow]")

    # Ensure the directory and file exist
    env_path.parent.mkdir(parents=True, exist_ok=True)
    if not env_path.exists():
        env_path.touch()

    # Save logic
    env_str = str(env_path)
    set_key(env_str, "GITHUB_TOKEN", github_token.strip(), quote_mode="always")
    set_key(env_str, "LLM_PROVIDER", llm_provider.strip(), quote_mode="always")
    
    if llm_provider == "gemini":
        set_key(env_str, "GEMINI_API_KEY", gemini_api_key.strip(), quote_mode="always")
    elif llm_provider == "ollama":
        set_key(env_str, "OLLAMA_MODEL", ollama_model.strip(), quote_mode="always")
        
    if configure_blockchain:
        set_key(env_str, "OPERATOR_WALLET_PRIVATE_KEY", private_key.strip(), quote_mode="always")
        set_key(env_str, "RPC_URL", rpc_url.strip(), quote_mode="always")
        set_key(env_str, "SKIP_BLOCKCHAIN", "false", quote_mode="always")
    else:
        set_key(env_str, "SKIP_BLOCKCHAIN", "true", quote_mode="always")

    console.rprint("\n[bold green]Configuration saved successfully![/bold green]\n")

def setup_config(force=False):
    """Checks if config exists, runs wizard if not, or if forced, and loads the env variables."""
    env_path = get_env_path()
    
    if force or not env_path.exists():
        run_setup_wizard(env_path)
        
    # Always load from the global config path
    load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    setup_config()
