import os
from rich import print as rprint

from backend.llm import analyze_and_plan

class PlannerAgent:
    def plan_resolution(self, issue_details, nudge=""):
        """
        Analyzes the issue and generates a technical action plan.
        """
        rprint(f"[bold yellow][PlannerAgent][/bold yellow] Technical analysis of issue #{issue_details['issue_id']}... {nudge}")
        plan = analyze_and_plan(issue_details, nudge=nudge)
        
        if plan:
            rprint(f"[bold yellow][PlannerAgent][/bold yellow] Plan generated: {plan.get('plan', 'N/A')}")
            rprint(f"[bold yellow][PlannerAgent][/bold yellow] Files to modify: {plan.get('files_to_modify', [])}")
            return plan
        else:
            rprint("[bold yellow][PlannerAgent][/bold yellow] [bold red]ERROR:[/bold red] Failed to generate an action plan.")
            return None
