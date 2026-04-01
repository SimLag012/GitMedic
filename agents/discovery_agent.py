import os
from github import Github
import sys
# Add parent directory to path so it can find config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import setup_config

setup_config()

class DiscoveryAgent:
    def __init__(self, github_token=None):
        self.token = github_token or os.getenv("GITHUB_TOKEN")
        if not self.token:
            print("[DiscoveryAgent] ERROR: GITHUB_TOKEN not found.")
        self.g = Github(self.token) if self.token else None
        self.cache_file = "logs/discovery_cache.json"
        if not os.path.exists("logs"):
            os.makedirs("logs")

    def search_high_priority_bugs(self):
        """
        Searches for open issues with the 'bug' label on Python of limited size.
        """
        if not self.g: return None
        
        print("[DiscoveryAgent] Searching GitHub for issues (small and simplified projects)...")
        
        # Check Cache
        import json
        import time
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r", encoding='utf-8') as f:
                cache = json.load(f)
                # Cache validity: 1 hour
                if time.time() - cache.get("timestamp", 0) < 3600:
                    print("[DiscoveryAgent] Utilizing cached results.")
                    return cache.get("issue")

        # Global query: open issues with 'bug' and 'good first issue' labels on Python (no size/star limits)
        query = "is:issue is:open label:bug label:\"good first issue\" language:python"
        issues = self.g.search_issues(query)
        
        # Load log to avoid duplicates
        processed_issues = []
        if os.path.exists("logs/agent_log.json"):
            try:
                with open("logs/agent_log.json", "r") as f:
                    logs = json.load(f)
                    processed_issues = [log["result"].split("#")[-1] for log in logs if "step" in log and log["step"] == "submission" or (log.get("step") == "execution" and "Success" in log.get("result", ""))]
            except: pass

        if issues.totalCount == 0:
            print("[DiscoveryAgent] No issues found.")
            return None
            
        # Find the first unprocessed issue
        issue_obj = None
        for i in range(min(issues.totalCount, 20)):
            current = issues[i]
            if str(current.number) not in processed_issues:
                issue_obj = current
                break
        
        if not issue_obj:
            print("[DiscoveryAgent] All found issues have already been processed.")
            return None
        issue_data = {
            "repo_name": issue_obj.repository.full_name,
            "repo_url": issue_obj.repository.clone_url,
            "issue_id": issue_obj.number,
            "title": issue_obj.title,
            "description": issue_obj.body
        }

        # Update Cache
        with open(self.cache_file, "w", encoding='utf-8') as f:
            json.dump({"timestamp": time.time(), "issue": issue_data}, f, indent=2)

        print(f"[DiscoveryAgent] Found Issue #{issue_obj.number} in {issue_obj.repository.full_name}")
        return issue_data

    def search_specific_repo_bugs(self, target_url):
        """
        Searches for an issue in a specific repository, 
        or parses a direct issue URL if provided.
        """
        if not self.g: return None

        print(f"[DiscoveryAgent] Searching issues for target: {target_url} ...")
        
        repo_name = target_url
        issue_number = None

        if "github.com/" in target_url:
            parts = target_url.split("github.com/")[-1].split("/")
            if len(parts) >= 2:
                repo_name = f"{parts[0]}/{parts[1]}"
                if len(parts) >= 4 and parts[2] == "issues":
                    issue_number = int(parts[3])
        
        print(f"[DiscoveryAgent] DEBUG: repo_name={repo_name}, issue_number={issue_number}")
        try:
            repo = self.g.get_repo(repo_name.strip())
            
            if issue_number:
                issue_obj = repo.get_issue(issue_number)
            else:
                # Find the first open issue with the bug label if possible, or any open issue
                query = f"repo:{repo_name} is:issue is:open label:bug"
                issues = self.g.search_issues(query)
                if issues.totalCount > 0:
                    issue_obj = issues[0]
                else:
                    # Fallback on open issues without labels
                    issues = repo.get_issues(state='open')
                    if issues.totalCount > 0:
                        issue_obj = issues[0]
                    else:
                        print("[DiscoveryAgent] No issues found in the specified repo.")
                        return None
                        
            issue_data = {
                "repo_name": repo.full_name,
                "repo_url": repo.clone_url,
                "issue_id": issue_obj.number,
                "title": issue_obj.title,
                "description": issue_obj.body
            }
            print(f"[DiscoveryAgent] Found Issue #{issue_obj.number} in {repo.full_name}")
            return issue_data
            
        except Exception as e:
            print(f"[DiscoveryAgent] ERROR while retrieving repo/issue: {e}")
            return None

    def get_file_list(self, work_dir):
        """
        Scans the working directory and returns a list of relevant files (Python).
        """
        file_list = []
        for root, dirs, files in os.walk(work_dir):
            if ".git" in root or "__pycache__" in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    rel_path = os.path.relpath(os.path.join(root, file), work_dir)
                    file_list.append(rel_path)
        # Increased limit for deeper repositories like pyqtgraph
        return file_list[:500]
