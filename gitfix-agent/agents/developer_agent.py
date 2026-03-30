import os
import uuid
import git
import shutil
from llm import generate_patch

class DeveloperAgent:
    def __init__(self, workspace_root):
        self.repos_dir = os.path.join(workspace_root, "repos")
        if not os.path.exists(self.repos_dir):
            os.makedirs(self.repos_dir)

    def _remove_readonly(self, func, path, excinfo):
        """Handler for shutil.rmtree on Windows for read-only files."""
        import stat
        os.chmod(path, stat.S_IWRITE)
        func(path)

    def implement_fix(self, issue, plan, retry_feedback=None, critic_advice=None, is_retry=False):
        """
        Clones, modifies, and commits the changes. 
        If is_retry=True, maintains current state to allow incremental corrections.
        """
        repo_url = issue["repo_url"]
        token = os.getenv("GITHUB_TOKEN")
        if token:
            repo_url = repo_url.replace("https://", f"https://{token}@")
            
        work_dir = os.path.join(self.repos_dir, f"issue_{issue['issue_id']}")
        
        repo = None
        if os.path.exists(work_dir):
            try:
                repo = git.Repo(work_dir)
                if not is_retry:
                    print(f"[DeveloperAgent] Resetting repository {work_dir} (New Plan)...")
                    repo.git.reset("--hard")
                    repo.git.clean("-fd")
                    try:
                        repo.git.checkout("master")
                    except:
                        try:
                            repo.git.checkout("main")
                        except:
                            pass
                    repo.git.pull() 
                else:
                    print(f"[DeveloperAgent] Maintaining repository state for incremental retry in {work_dir}...")
            except Exception as e:
                if not is_retry:
                    print(f"[DeveloperAgent] Reset failed: {e}. Attempting removal...")
                    try:
                        shutil.rmtree(work_dir, onerror=self._remove_readonly)
                    except:
                        work_dir = work_dir + "_retry"
                else:
                    print(f"[DeveloperAgent] WARNING: Error accessing repo during retry: {e}. Proceeding with caution.")
        
        if not repo:
            try:
                repo = git.Repo.clone_from(repo_url, work_dir)
            except Exception as e:
                print(f"[DeveloperAgent] Clone ERROR: {e}")
                return None

        branch_name = f"fix-bug-{issue['issue_id']}-{uuid.uuid4().hex[:6]}"
        repo.git.checkout("-b", branch_name)

        files_to_modify = plan.get("files_to_modify", [])
        modified_files = []
        for fpath in files_to_modify:
            full_path = os.path.join(work_dir, fpath)
            if not os.path.exists(full_path):
                print(f"[DeveloperAgent] WARNING: {fpath} does not exist.")
                continue
            
            with open(full_path, "r", encoding='utf-8') as f:
                content = f.read()
            
            # Context extraction ... (keeps existing logic)
            patch_context = content
            # ... SNIP (logic that sets patch_context)
            
            # GENERATION WITH CRITIC ADVICE
            print(f"[DeveloperAgent] Generating patch for {fpath}...")
            from llm import generate_patch
            
            new_content = None
            patch_error = None
            for p_attempt in range(3):
                current_feedback = retry_feedback or ""
                if patch_error:
                    current_feedback += f"\n\nCRITICAL FIX NEEDED: The previous patch application failed with error:\n{patch_error}\nPlease fix the <search> block to exactly match the original file."
                    
                new_content = generate_patch(
                    content, plan, 
                    feedback=current_feedback.strip() if current_feedback.strip() else None, 
                    context_snippet=patch_context if patch_context != content else content,
                    critic_advice=critic_advice
                )
                
                if not new_content:
                    patch_error = "No output from LLM."
                    continue
                    
                if new_content.startswith("FORMAT_ERROR"):
                    patch_error = new_content
                    print(f"[DeveloperAgent] {patch_error} (Attempt {p_attempt+1}/3)")
                    new_content = None
                    continue
                    
                if len(new_content) < len(content) * 0.1 and len(content) > 1000:
                    patch_error = "Output truncated."
                    print(f"[DeveloperAgent] TRUNCATION Rejected. (Attempt {p_attempt+1}/3)")
                    new_content = None
                    continue
                
                if new_content.strip() == content.strip():
                    patch_error = "New code identical to old code (null patch generated)."
                    print(f"[DeveloperAgent] No modifications made. (Attempt {p_attempt+1}/3)")
                    new_content = None
                    continue
                    
                # Success
                break
                
            if not new_content:
                print(f"[DeveloperAgent] Abandoning {fpath} due to persistent patch format errors.")
                continue

            with open(full_path, "w", encoding='utf-8') as f:
                f.write(new_content)
            modified_files.append(full_path)
        
        if not modified_files: return None

        # Smart Guardrail: Uses Planner's dynamic limits
        guardrails = plan.get("guardrails", {})
        max_f = guardrails.get("max_files", 3)
        max_l = guardrails.get("max_lines", 2000)

        if len(modified_files) > max_f:
            print(f"[DeveloperAgent] ERROR: Too many files modified ({len(modified_files)} > {max_f}).")
            return None

        try:
            stats = repo.git.diff("--shortstat")
            # Example output: " 1 file changed, 15 insertions(+), 5 deletions(-)"
            print(f"[DeveloperAgent] Modification statistics: {stats.strip()}")
            
            # A raw but effective calculation to sum changes
            total_changes = 0
            import re
            numbers = re.findall(r'\d+', stats)
            if len(numbers) >= 2:
                total_changes = sum(int(n) for n in numbers[1:]) # Skips the number of files
            
            if total_changes > max_l:
                print(f"[DeveloperAgent] ERROR: Too many modifications ({total_changes} > {max_l}).")
                return None
        except Exception as e:
            print(f"[DeveloperAgent] WARNING: Unable to calculate diff statistics: {e}")

        repo.git.add(".")
        repo.index.commit(f"AutoDevAgent: fix for issue #{issue['issue_id']}")
        
        return {
            "work_dir": work_dir,
            "modified_files": modified_files,
            "repo_obj": repo,
            "branch_name": branch_name,
            "total_changes": total_changes
        }
