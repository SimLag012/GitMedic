import argparse
from blockchain import register_agent_identity
from agent import GitMedicOrchestrator
import os

from rich import print as rprint
from config import setup_config

def main():
    parser = argparse.ArgumentParser(description="GitMedic CLI - Autonomous Bug Fixing Agent")
    parser.add_argument("-r", "--random", action="store_true", help="Discover and fix a random high-priority bug")
    parser.add_argument("repo_link", nargs="?", help="Specific repository link or issue link to fix")
    parser.add_argument("--pull", action="store_true", help="Force submit a Pull Request after fixing the bug")
    parser.add_argument("--no-pull", action="store_true", help="Do not create a Pull Request after fixing the bug")
    parser.add_argument("--config", action="store_true", help="Launch the interactive configuration wizard")
    parser.add_argument("--provider", choices=["ollama", "gemini"], help="Select the LLM provider (overrides config)")
    parser.add_argument("--clean", action="store_true", help="Delete all locally cloned repositories and logs")
    args = parser.parse_args()

    # Logic for cleaning local data
    if args.clean:
        import shutil
        base_dir = os.path.dirname(os.path.abspath(__file__))
        repos_dir = os.path.join(base_dir, "repos")
        logs_dir = os.path.join(base_dir, "logs")
        
        if os.path.exists(repos_dir):
            rprint(f"[bold yellow]Deleting {repos_dir}...[/bold yellow]")
            shutil.rmtree(repos_dir)
            os.makedirs(repos_dir)
            
        if os.path.exists(logs_dir):
            rprint(f"[bold yellow]Deleting {logs_dir}...[/bold yellow]")
            shutil.rmtree(logs_dir)
            os.makedirs(logs_dir)
            
        rprint("[bold green]Local data cleaned successfully.[/bold green]")
        return

    # Apply the provider if specified via CLI
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider

    # Initialize configuration (Requests interactive API Keys or loads them)
    setup_config(force=args.config)

    # If the user only asked for setup, exit after doing it
    if args.config:
        return

    # Apply flags to the system by setting environment variables
    if args.pull:
        os.environ["SKIP_SUBMIT"] = "false"
    elif args.no_pull:
        os.environ["SKIP_SUBMIT"] = "true"

    # Set current working directory to the file's directory to avoid relative path issues
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(base_dir)

    # Ensure the logs and repos directories exist
    if not os.path.exists("logs"):
        os.mkdir("logs")
    if not os.path.exists("repos"):
        os.mkdir("repos")

    if not args.repo_link and not args.random:
        parser.print_help()
        return

    rprint("[bold cyan]========================================[/bold cyan]")
    rprint("[bold white]    GitMedic Multi-Agent System 1.0     [/bold white]")
    rprint("[bold white]       By Simone Laganà                 [/bold white]")
    rprint("[bold cyan]========================================[/bold cyan]\n")
    # One-time registration of the ERC-8004 identity
    register_agent_identity()
    
    # Initialize the Orchestrator
    agent = GitMedicOrchestrator()
    
    if args.repo_link:
        rprint(f"[bold green]Starting GitMedic for specific target:[/bold green] {args.repo_link}")
        agent.run(target_url=args.repo_link)
    elif args.random:
        rprint("[bold green]Starting GitMedic in discovery mode (random bug)...[/bold green]")
        agent.run(discovery_mode=True)

if __name__ == "__main__":
    main()