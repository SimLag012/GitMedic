import os
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
    console.print("\n[bold cyan]=== GitMedic First-Time Setup ===[/bold cyan]")
    console.print("Welcome to GitMedic! Let's configure your agent.\n")
    console.print("This setup will save your API keys globally to:")
    console.print(f"[bold yellow]{env_path}[/bold yellow]\n")

    # GitHub Token - Mandatory
    github_token = ""
    while not github_token.strip():
        github_token = Prompt.ask("[bold green]GitHub Personal Access Token[/bold green] (repo scope required)")
        if not github_token.strip():
            console.print("[red]Error: GitHub Token is required.[/red]")

    llm_provider = Prompt.ask("[bold green]LLM Provider[/bold green]", choices=["ollama", "gemini"], default="ollama")
    
    gemini_api_key = ""
    ollama_model = "gpt-oss:120b-cloud"
    if llm_provider == "gemini":
        while not gemini_api_key.strip():
            gemini_api_key = Prompt.ask("[bold green]Gemini API Key[/bold green]")
            if not gemini_api_key.strip():
                console.print("[red]Error: Gemini API Key is required for the Gemini provider.[/red]")
    elif llm_provider == "ollama":
        ollama_model = Prompt.ask("[bold green]Ollama Model[/bold green]", default="gpt-oss:120b-cloud")

    console.print("\n[bold cyan]--- Ethereum Agent Identity (ERC-8004) ---[/bold cyan]")
    console.print("GitMedic can register its identity on-chain for secure agent-to-agent verification.")
    configure_blockchain = Confirm.ask("Do you want to enable Ethereum identity registration?")
    
    private_key = ""
    rpc_url = ""
    if configure_blockchain:
        while not private_key.strip():
            private_key = Prompt.ask("[bold green]Agent Wallet Private Key[/bold green]")
            if not private_key.strip():
                console.print("[red]Error: Private Key is required if blockchain is enabled.[/red]")
        
        while not rpc_url.strip():
            rpc_url = Prompt.ask("[bold green]RPC URL[/bold green] (e.g. https://sepolia.infura.io/v3/...)")
            if not rpc_url.strip():
                console.print("[red]Error: RPC URL is required if blockchain is enabled.[/red]")
    else:
        console.print("[yellow]Blockchain registration disabled. (SKIP_BLOCKCHAIN=true)[/yellow]")

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

    console.print("\n[bold green]Configuration saved successfully![/bold green]\n")

def setup_config(force=False):
    """Checks if config exists, runs wizard if not, or if forced, and loads the env variables."""
    env_path = get_env_path()
    
    if force or not env_path.exists():
        run_setup_wizard(env_path)
        
    # Always load from the global config path
    load_dotenv(dotenv_path=env_path)

if __name__ == "__main__":
    setup_config()
