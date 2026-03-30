import argparse
from blockchain import register_agent_identity
from agent import GitFixOrchestrator
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
    args = parser.parse_args()

    # Inizializza la configurazione (Richiede API Keys interattive o le carica)
    setup_config(force=args.config)

    # Se l'utente ha solo chiesto il setup, esci dopo averlo fatto
    if args.config:
        return

    # Applica i flag al sistema impostando la variabile d'ambiente
    if args.pull:
        os.environ["SKIP_SUBMIT"] = "false"
    elif args.no_pull:
        os.environ["SKIP_SUBMIT"] = "true"

    # Imposta la directory di lavoro su quella del file per evitare problemi con path relativi
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
    rprint("[bold white]    GitFix Multi-Agent System 1.0       [/bold white]")
    rprint("[bold cyan]========================================[/bold cyan]\n")
    # One-time registration of the ERC-8004 identity
    register_agent_identity()
    
    # Initialize the Orchestrator
    agent = GitFixOrchestrator()
    
    if args.repo_link:
        rprint(f"[bold green]Starting GitMedic for specific target:[/bold green] {args.repo_link}")
        agent.run(target_url=args.repo_link)
    elif args.random:
        rprint("[bold green]Starting GitMedic in discovery mode (random bug)...[/bold green]")
        agent.run(discovery_mode=True)

if __name__ == "__main__":
    main()