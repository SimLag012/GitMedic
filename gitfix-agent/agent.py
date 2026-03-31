import os
import json
from datetime import datetime
from github import Github

# Import specialized agents
from agents.discovery_agent import DiscoveryAgent
from agents.planner_agent import PlannerAgent
from agents.developer_agent import DeveloperAgent
from agents.verifier_agent import VerifierAgent

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.live import Live
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.layout import Layout
from rich import print as rprint

console = Console()

LOG_FILE = "logs/agent_log.json"
MAX_GITHUB_REQS = 30

class GitFixOrchestrator:
    def __init__(self):
        self.logs = []
        self.req_count = 0
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Initialize the agent team
        self.discovery_agent = DiscoveryAgent()
        self.planner_agent = PlannerAgent()
        self.developer_agent = DeveloperAgent(self.base_dir)
        self.verifier_agent = VerifierAgent()
        
        # Session Metrics
        import time
        self.metrics = {
            "issues_scanned": 0,
            "fixes_attempted": 0,
            "successes": 0,
            "total_lines_modified": 0,
            "start_time": time.time()
        }

        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding='utf-8') as f:
                    self.logs = json.load(f)
            except:
                pass

    def log_action(self, step, agent_name, result, decision=None):
        entry = {
            "step": step,
            "agent": agent_name,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        if decision:
            entry["decision"] = decision
        self.logs.append(entry)
        with open(LOG_FILE, "w", encoding='utf-8') as f:
            json.dump(self.logs, f, indent=2)

    def print_dashboard(self):
        import time
        elapsed = time.time() - self.metrics["start_time"]
        
        table = Table(title="[bold blue]GITFIX SESSION DASHBOARD[/bold blue]", box=None)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="magenta")
        
        table.add_row("Issues Scanned", str(self.metrics['issues_scanned']))
        table.add_row("Fixes Attempted", str(self.metrics['fixes_attempted']))
        table.add_row("Successes", f"[bold green]{self.metrics['successes']}[/bold green]")
        table.add_row("Lines Modified", str(self.metrics['total_lines_modified']))
        table.add_row("Execution Time", f"{elapsed:.2f}s")
        
        console.print(Panel(table, border_style="blue", padding=(1, 2)))

    def run(self, target_url=None, discovery_mode=False):
        if not discovery_mode:
            self._run_once(target_url=target_url, discovery_mode=False)
            return
            
        rprint("\n[bold cyan]=== GitMedic INFINITE RESILIENCE LOOP ===[/bold cyan]")
        import time
        attempt = 1
        while True:
            rprint(f"\n[bold magenta]*** RECOVERY/DISCOVERY CYCLE {attempt} ***[/bold magenta]")
            cache_file = "logs/discovery_cache.json"
            if os.path.exists(cache_file):
                try: os.remove(cache_file)
                except: pass
                
            status = self._run_once(target_url=target_url, discovery_mode=True)
            if status == True:
                rprint("[bold green] GitMedic successfully completed a fix. Exiting loop.[/bold green]")
                break
            elif status == "FATAL":
                rprint("[bold red] Stopping GitMedic due to a critical configuration error.[/bold red]")
                break
            
            rprint("[bold yellow] Cycle failed (issue might be already fixed or invalid). Retrying with a new bug...[/bold yellow]")
            attempt += 1
            time.sleep(2)

    def _run_once(self, target_url=None, discovery_mode=False):
        from llm import get_provider, check_ollama, start_ollama
        provider = get_provider()
        
        rprint("\n[bold cyan]=== GitFix Multi-Agent System Started ===[/bold cyan]\n")
        
        # Initial LLM status check
        if provider == "ollama":
            with console.status("[bold yellow]Checking Ollama status...") as status:
                is_running, msg = check_ollama()
                if not is_running:
                    status.update("[bold yellow]Ollama not found. Attempting to start server...")
                    success, start_msg = start_ollama()
                    if success:
                        rprint(f"[bold green]LLM READY:[/bold green] {start_msg}")
                    else:
                        rprint(f"[bold red]CRITICAL ERROR:[/bold red] {start_msg}")
                        rprint("[yellow]Please start 'ollama serve' manually.[/yellow]")
                        return False
                else:
                    rprint(f"[bold green]LLM READY:[/bold green] {msg}")
        else:
            rprint(f"[bold green]LLM READY:[/bold green] Using Gemini API provider.")
        
        # Check for mandatory GITHUB_TOKEN before discovery
        if not os.getenv("GITHUB_TOKEN"):
            rprint("[bold red]CRITICAL ERROR:[/bold red] GITHUB_TOKEN not found in environment variables.")
            rprint("[yellow]Please run 'gitmedic --config' to set up your GitHub Personal Access Token.[/yellow]")
            return "FATAL"

        # 1. DISCOVERY
        if target_url:
            issue = self.discovery_agent.search_specific_repo_bugs(target_url)
        elif discovery_mode:
            issue = self.discovery_agent.search_high_priority_bugs()
        else:
            rprint("[bold red]No target or discovery mode specified.[/bold red]")
            return False

        if not issue:
            self.log_action("discovery", "DiscoveryAgent", "No issues found", "Waiting for next cycle")
            return False
        
        self.log_action("discovery", "DiscoveryAgent", f"Found issue #{issue['issue_id']}", "Selected target issue")
        self.metrics["issues_scanned"] += 1

        # Pre-clone or check existing to get file structure for the Planner
        work_dir = os.path.join(self.base_dir, "repos", f"issue_{issue['issue_id']}")
        if not os.path.exists(work_dir):
            rprint(f"[bold yellow][Orchestrator][/bold yellow] Downloading repository structure for Planner...")
            # Use a dummy plan to trigger cloning
            self.developer_agent.implement_fix(issue, {"plan": "PRE-CLONE", "files_to_modify": []})
        
        file_list = self.discovery_agent.get_file_list(work_dir)
        issue["file_list"] = file_list
        
        # 2. PLANNING (Swarm Mode - Parallel Execution)
        rprint("[bold blue][Orchestrator][/bold blue] Starting Swarm Planning: Generating parallel strategies...")
        from concurrent.futures import ThreadPoolExecutor
        
        nudges = [
            "Focus on extreme precision and modifying minimal files.",
            "Focus on a robust and comprehensive solution."
        ]
        
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(self.planner_agent.plan_resolution, issue, nudge=n) for n in nudges]
            candidate_plans = [f.result() for f in futures if f.result()]

        if not candidate_plans:
            self.log_action("planning", "PlannerAgent", "Failed to create any plan")
            return False
            
        # Selection of the best plan (the most concise one)
        candidate_plans.sort(key=lambda x: x.get("estimated_lines", 999))
        plan = candidate_plans[0]
        
        rprint(f"[bold blue][Orchestrator][/bold blue] Swarm Selection: Choosing most efficient strategy ({plan.get('estimated_lines', 'N/A')} lines).")
        
        # --- PLAN VALIDATION (Anti-Hallucination) ---
        valid_files = []
        hallucinated = False
        for f in plan.get("files_to_modify", []):
            if os.path.exists(os.path.join(work_dir, f)):
                valid_files.append(f)
            else:
                hallucinated = True
                print(f"[Orchestrator] WARNING: Hallucinated file path detected: {f}. Attempting correction...")
                # Search for file with identical basename in the real file_list
                base_name = os.path.basename(f)
                matches = [rf for rf in issue.get("file_list", []) if os.path.basename(rf) == base_name]
                if matches:
                    print(f"[Orchestrator] Automatic correction: {f} -> {matches[0]}")
                    valid_files.append(matches[0])
                else:
                    print(f"[Orchestrator] Unable to find match for {f}.")
        
        if hallucinated:
            plan["files_to_modify"] = valid_files
            if not valid_files:
                print("[Orchestrator] ERROR: No files in the plan actually exist. Failure.")
                return False

        self.log_action("planning", "PlannerAgent", "Plan validated & corrected", plan.get("rationale"))
        
        # 3. EXECUTION & VERIFICATION (with Multi-Plan Fallback & "Critic" Loop)
        rprint(f"[bold blue][Orchestrator][/bold blue] Beginning execution phase on {len(candidate_plans)} candidate plans.")
        
        execution_data = None
        global_failures = [] # For the Planner if Deep Retry is needed
        
        for plan_idx, plan in enumerate(candidate_plans):
            rationale = plan.get('rationale', 'No rationale provided')
            rprint(f"\n[bold green]>>> ATTEMPTING PLAN #{plan_idx + 1}:[/bold green] {rationale[:100]}...")
            
            cumulative_feedback = []
            critic_advice = None
            verified = False
            attempt = 0
            app_fail_streak = 0
            # SUCCESS-ORIENTED RESILIENCE LOOP: Continues until it works
            while not verified and attempt < 15:
                attempt += 1
                rprint(f"\n[bold yellow]--- Plan {plan_idx+1}, Attempt {attempt} (Smart Resilience Mode) ---[/bold yellow]")
                self.metrics["fixes_attempted"] += 1
                
                feedback_context = "\n".join(cumulative_feedback) if cumulative_feedback else None
                
                # Implementation with Critic Advice & Stateful Retries
                execution_data = self.developer_agent.implement_fix(
                    issue, plan, 
                    retry_feedback=feedback_context,
                    critic_advice=critic_advice,
                    is_retry=(attempt > 1)
                )
                
                if not execution_data:
                    app_fail_streak += 1
                    err = f"Format/Application failed at attempt {attempt}."
                    cumulative_feedback.append(err)
                    
                    if app_fail_streak >= 3:
                        print("[Orchestrator] Too many consecutive patch formatting errors. Abandoning this plan.")
                        break 
                        
                    critic_advice = "CRITICAL WARNING: The previous patch format was invalid and could not be applied. Ensure your <search> block EXACTLY matches the file content."
                    continue
                else:
                    app_fail_streak = 0
                    
                verified, error_msg = self.verifier_agent.verify(execution_data, issue)
                if verified:
                    print(f"[Orchestrator] FINAL SUCCESS: Plan #{plan_idx+1} resolved at attempt {attempt}!")
                    self.log_action("execution", "DeveloperAgent", f"Success with Plan {plan_idx+1}")
                    break
                else:
                    # Call to CRITIC to understand what to modify
                    from llm import analyze_failure
                    last_code = ""
                    if execution_data.get("modified_files"):
                        with open(execution_data["modified_files"][0], "r", encoding='utf-8') as f:
                            last_code = f.read()
                    
                    print(f"[Orchestrator] Logical/Syntax failure at attempt {attempt}. Consulting Critic...")
                    current_critic_advice = analyze_failure(last_code, error_output=error_msg)
                    
                    # Stagnation detection (same analysis repeated)
                    if critic_advice and current_critic_advice.strip() == critic_advice.strip():
                        print("[Orchestrator] WARNING: Critic is repeating identical advice. Shifting correction strategy...")
                        current_critic_advice += "\n\nCRITICAL DIRECTIVE: Your previous attempt based on this advice still FAILED. You MUST try a completely different approach!"
                    
                    critic_advice = current_critic_advice
                    print(f"[Critic] Analysis for the next cycle: {critic_advice}")

                    err = f"Attempt {attempt} verification failed:\n{error_msg}"
                    cumulative_feedback.append(err)
                    global_failures.append(err)
                    
                    # Reset for the next incremental attempt
                    execution_data = None 
            
            if verified:
                break
            else:
                print(f"[Orchestrator] Plan #{plan_idx+1} abandoned after {attempt} unsuccesful attempts.")

        # DEEP RETRY: If everything fails, try re-planning with historical data
        if not execution_data:
            print("\n[Orchestrator] DEEP RETRY PHASE: All initial plans failed. Reconstructing strategy...")
            from llm import analyze_and_plan
            past_errs = "\n".join(global_failures[-5:]) # Last 5 errors
            new_plan = analyze_and_plan(issue, nudge="PERFORM A COMPLETE RESET. Analyze past errors and propose a completely different solution.", past_failures=past_errs)
            
            if new_plan:
                print(f"[Orchestrator] New emergency plan generated. Final attempt...")
                # ... could implement recursion or final loop, executing single attempt for now
                execution_data = self.developer_agent.implement_fix(issue, new_plan, retry_feedback=past_errs)
                if execution_data:
                    verified, _ = self.verifier_agent.verify(execution_data, issue)
                    if verified:
                        print("[Orchestrator] DEEP RETRY SUCCESSFUL!")
                    else:
                        execution_data = None

        if not execution_data:
            print("[Orchestrator] ERROR: All plans and attempts have failed.")
            self._generate_failure_report(issue, candidate_plans[0], "All plans failed")
            return False
        
        # 5. SUBMISSION (Orchestrator handles final PR for safety)
        self.submit_pr(issue, execution_data)
        
        self.metrics["successes"] += 1
        self.metrics["total_lines_modified"] += execution_data.get("total_changes", 0)
        self.print_dashboard()
        return True

    def submit_pr(self, issue, execution_data):
        print("\n--- SUBMIT ---")
        if os.getenv("SKIP_SUBMIT", "false").lower() == "true":
            print("[Orchestrator] SKIP_SUBMIT=true: Bypassing Pull Request creation.")
            return

        repo_obj = execution_data.get("repo_obj")
        branch_name = execution_data.get("branch_name")
        
        try:
            print(f"[Orchestrator] Pushing branch {branch_name}...")
            repo_obj.git.push("origin", branch_name)
            
            token = os.getenv("GITHUB_TOKEN")
            g = Github(token)
            github_repo = g.get_repo(issue['repo_name'])
            
            pr = github_repo.create_pull(
                title=f"Fix bug in {issue['title']}",
                body=f"Automated fix by GitFix Multi-Agent System.\n\nPlan: {issue.get('plan_desc', '')}",
                head=branch_name,
                base=github_repo.default_branch
            )
            print(f"[Orchestrator] PR Created: {pr.html_url}")
            self.log_action("submission", "Orchestrator", f"PR Created: {pr.html_url}")
        except Exception as e:
            print(f"[Orchestrator] PR ERROR: {e}")
            self.log_action("submission", "Orchestrator", "Failed to create PR", str(e))

    def _generate_failure_report(self, issue, plan, error):
        report_path = os.path.join("logs", f"failure_report_{issue['issue_id']}.json")
        report = {
            "issue_id": issue["issue_id"],
            "title": issue["title"],
            "plan_attempted": plan,
            "last_error": error,
            "timestamp": datetime.now().isoformat()
        }
        with open(report_path, "w", encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"[Orchestrator] Failure report generated: {report_path}")
