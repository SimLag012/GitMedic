import argparse
import os

from rich import print as rprint
from rich.panel import Panel
from rich.align import Align
from backend.config import setup_config
from backend.blockchain import register_agent_identity
from backend.agent import GitMedicOrchestrator

try:
    from rich_argparse import RichHelpFormatter
    RichHelpFormatter.styles["argparse.args"] = "cyan"
    RichHelpFormatter.styles["argparse.groups"] = "bold magenta"
    RichHelpFormatter.styles["argparse.help"] = "white"
    RichHelpFormatter.styles["argparse.metavar"] = "green"
    RichHelpFormatter.styles["argparse.prog"] = "bold cyan"
    formatter_class = RichHelpFormatter
except ImportError:
    formatter_class = argparse.HelpFormatter


def _print_banner():
    logo = """[bold cyan]
   _____ _ _   __  __          _ _      
  / ____(_) | |  \\/  |        | (_)     
 | |  __ _| |_| \\  / | ___  __| |_  ___ 
 | | |_ | | __| |\\/| |/ _ \\/ _` | |/ __|
 | |__| | | |_| |  | |  __/ (_| | | (__ 
  \\_____|_|\\__|_|  |_|\\___|\\__,_|_|\\___|[/bold cyan]"""
    header = f"{logo}\n\n[white]Multi-Agent System 1.0[/white]\n[italic bright_black]By Simone Lagana[/italic bright_black]"
    rprint(Panel(Align.center(header), border_style="cyan", padding=(1, 5)))
    rprint()


def main():
    parser = argparse.ArgumentParser(
        description="[bold cyan]GitMedic CLI[/bold cyan] - Autonomous Bug Fixing Agent",
        formatter_class=formatter_class
    )
    parser.add_argument("-r", "--random", action="store_true", help="Discover and fix a random high-priority bug")
    parser.add_argument("repo_link", nargs="?", help="Specific repository link or issue link to fix")
    parser.add_argument("--pull", action="store_true", help="Force submit a Pull Request after fixing the bug")
    parser.add_argument("--no-pull", action="store_true", help="Do not create a Pull Request after fixing the bug")
    parser.add_argument("--config", action="store_true", help="Launch the interactive configuration wizard")
    parser.add_argument("--provider", choices=["ollama", "gemini"], help="Select the LLM provider (overrides config)")
    parser.add_argument("--clean", action="store_true", help="Delete all locally cloned repositories and logs")
    args = parser.parse_args()

    # Always show the banner
    _print_banner()

    # --- CLEAN ---
    if args.clean:
        import shutil, stat
        base_dir = os.getcwd()

        def _remove_readonly(func, path, excinfo):
            os.chmod(path, stat.S_IWRITE)
            func(path)

        for folder in ["repos", "logs"]:
            target = os.path.join(base_dir, folder)
            if os.path.exists(target):
                rprint(f"[bold yellow]Deleting {target}...[/bold yellow]")
                shutil.rmtree(target, onerror=_remove_readonly)
                os.makedirs(target)
        rprint("[bold green]Local data cleaned successfully.[/bold green]")
        return

    # --- PROVIDER OVERRIDE ---
    if args.provider:
        os.environ["LLM_PROVIDER"] = args.provider

    # --- CONFIG ---
    setup_config(force=args.config)
    if args.config:
        return

    # --- FLAGS ---
    if args.pull:
        os.environ["SKIP_SUBMIT"] = "false"
    elif args.no_pull:
        os.environ["SKIP_SUBMIT"] = "true"

    # --- WORKSPACE ---
    base_dir = os.getcwd()
    for folder in ["logs", "repos"]:
        os.makedirs(os.path.join(base_dir, folder), exist_ok=True)

    # --- HELP if no action ---
    if not args.repo_link and not args.random:
        parser.print_help()
        return

    # --- RUN ---
    register_agent_identity()
    agent = GitMedicOrchestrator(base_dir=base_dir)

    if args.repo_link:
        rprint(f"[bold green]Starting GitMedic for specific target:[/bold green] {args.repo_link}")
        agent.run(target_url=args.repo_link)
    elif args.random:
        rprint("[bold green]Starting GitMedic in discovery mode (random bug)...[/bold green]")
        agent.run(discovery_mode=True)


if __name__ == "__main__":
    main()
