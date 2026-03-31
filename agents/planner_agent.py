import os
from llm import analyze_and_plan

class PlannerAgent:
    def plan_resolution(self, issue_details, nudge=""):
        """
        Analyzes the issue and generates a technical action plan.
        """
        print(f"[PlannerAgent] Technical analysis of issue #{issue_details['issue_id']}... {nudge}")
        plan = analyze_and_plan(issue_details, nudge=nudge)
        
        if plan:
            print(f"[PlannerAgent] Plan generated: {plan.get('plan', 'N/A')}")
            print(f"[PlannerAgent] Files to modify: {plan.get('files_to_modify', [])}")
            return plan
        else:
            print("[PlannerAgent] ERROR: Failed to generate an action plan.")
            return None
