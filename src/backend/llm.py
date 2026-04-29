import os
from rich import print as rprint
from rich.console import Console

console = Console()

import json
import requests
from backend.config import setup_config

setup_config()

# Global Guardrails
MAX_FILES_MODIFIED = 3
MAX_LINES_MODIFIED = 5000

def get_provider():
    return os.getenv("LLM_PROVIDER", "gemini").lower()

def ask_gemini(prompt):
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        rprint("[bold purple][GEMINI LOG][/bold purple] [bold red]ERROR:[/bold red] GEMINI_API_KEY not found in environment.")
        return None
    
    genai.configure(api_key=api_key)
    
    # Discovery has shown that this account has access to models like 2.0 and 2.5.
    # Trying the most modern ones available in the list.
    for model_name in ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro"]:
        try:
            with console.status(f"[bold purple][GEMINI LOG][/bold purple] Requesting {model_name}..."):
                # Note: The library adds 'models/' prefix automatically if missing
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
            
            # Check if the response was blocked by safety filters
            if hasattr(response, 'candidates') and response.candidates:
                if response.candidates[0].finish_reason == 3: # 3 is SAFETY
                    rprint(f"[bold purple][GEMINI LOG][/bold purple] [bold red]ERROR:[/bold red] Content generation blocked by safety filters (model: {model_name}).")
                    return None
                return response.text
            else:
                # Maybe it blocked before generating candidates
                if hasattr(response, 'prompt_feedback') and response.prompt_feedback:
                     rprint(f"[bold purple][GEMINI LOG][/bold purple] [bold red]ERROR:[/bold red] Prompt feedback for {model_name}: {response.prompt_feedback}")
                continue # Try next model
        except Exception as e:
            if "429" in str(e):
                import time
                rprint(f"[bold purple][GEMINI LOG][/bold purple] Quota exceeded (429) for {model_name}. Waiting 60 seconds to retry...")
                time.sleep(60)
                try:
                    # Retry once after waiting
                    response = model.generate_content(prompt)
                    if hasattr(response, 'candidates') and response.candidates:
                        return response.text
                except Exception as retry_e:
                    rprint(f"[bold purple][GEMINI LOG][/bold purple] Retry failed for {model_name}: {str(retry_e)}")
                continue # Try next model or fail
            if "404" in str(e):
                # Silent skip for 404 to try next model
                continue
            rprint(f"[bold purple][GEMINI LOG][/bold purple] ERROR during Gemini {model_name} call: {str(e)}")
            return None
    
    rprint("[bold purple][GEMINI LOG][/bold purple] CRITICAL [bold red]ERROR:[/bold red] All Gemini models (flash and pro) returned 404 or failed.")
    return None

def start_ollama():
    """
    Attempts to start 'ollama serve' in a separate background process.
    """
    import subprocess
    import time
    try:
        # Start ollama serve in background (Windows compatibility)
        rprint("[bold purple][LLM LOG][/bold purple] Attempting automatic startup of 'ollama serve' via CMD...")
        subprocess.Popen("ollama serve", 
                         shell=True,
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL,
                         creationflags=0x10 if os.name == 'nt' else 0) # 0x10 is CREATE_NEW_CONSOLE
        
        # Wait for the server to warm up
        for i in range(10):
            time.sleep(2)
            is_running, _ = check_ollama()
            if is_running:
                return True, "Ollama started successfully."
        return False, "Ollama failed to start within the timeout period."
    except Exception as e:
        return False, f"Unable to start Ollama: {str(e)}"

def check_ollama():
    """
    Verifies if the Ollama server is running and listening.
    """
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=2)
        if response.status_code == 200:
            return True, "Ollama is running."
        else:
            return False, f"Ollama returned status code {response.status_code}."
    except requests.exceptions.ConnectionError:
        return False, "Ollama server NOT found."
    except Exception as e:
        return False, f"Error checking Ollama: {str(e)}"

def ask_ollama(prompt):
    try:
        import ollama
        import time
        model_name = os.getenv("OLLAMA_MODEL", "codellama")
        
        # Preemptive Ollama status check
        is_running, status_msg = check_ollama()
        if not is_running:
            rprint(f"[bold purple][LLM LOG][/bold purple] [bold red]ERROR:[/bold red] {status_msg}")
            return None

        rprint(f"[bold purple][LLM LOG][/bold purple] Sending request to Ollama (model: {model_name})...")
        start_time = time.time()
        
        with console.status(f"[bold purple][LLM LOG][/bold purple] Generating with Ollama {model_name}..."):
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": prompt}]
            )
        
        elapsed = time.time() - start_time
        rprint(f"[bold purple][LLM LOG][/bold purple] Response received from Ollama in {elapsed:.2f} seconds.")
        return response["message"]["content"]
    except Exception as e:
        rprint("[bold purple][LLM LOG][/bold purple] Critical error during Ollama execution:", e)
        return None

def ask_llm(prompt):
    provider = get_provider()
    # rprint(f"Using provider: {provider}") # Too verbose
    if provider == "ollama":
        return ask_ollama(prompt)
    else:
        return ask_gemini(prompt)

def analyze_and_plan(issue_details, codebase_context="", nudge="", past_failures=None):
    """
    Analyzes the issue and plans the fix. Learns from past failures if provided.
    """
    file_list_str = "\n".join(issue_details.get("file_list", []))
    failure_context = f"\n[bold yellow]WARNING:[/bold yellow] The following attempts have FAILED. Analyze them to PREVENT identical errors:\n{past_failures}" if past_failures else ""
    
    prompt = f"""
    You are the Lead Engineer (Planner Agent) for an AI development team.
    Your objective is to resolve this GitHub bug decisively.
    {nudge}
    {failure_context}
    
    IMPORTANT: Use EXACT file paths as listed below.
    Available files:
    {file_list_str}
    
    GUIDELINES:
    1. **Learning**: If past errors persist (NameError, AssertionError), change strategy radically.
    2. **Minimalism**: Modify strictly what is necessary.
    3. **Precision**: Identify the correct file and precise location.
    
    Issue Title: {issue_details['title']}
    Issue Description: {issue_details['description']}
    
    Context:\n{codebase_context}
    
    Output strictly in JSON format:
    {{
        "files_to_modify": ["path/file.py"],
        "plan": "Detailed strategy",
        "rationale": "Reasoning why this iteration will succeed",
        "guardrails": {{"max_files": 2, "max_lines": 500}}
    }}
    """
    # Parsing logic
    text = ask_llm(prompt)
    if not text: return None
    try:
        if "```" in text:
            parts = text.split("```")
            for part in parts:
                if part.strip().startswith("json"):
                    text = part.strip()[4:]
                    break
                elif part.strip().startswith("{"):
                    text = part.strip()
                    break
        text = text.strip()
        start = text.find('{')
        end = text.rfind('}') + 1
        if start != -1 and end != 0:
            text = text[start:end]
        plan = json.loads(text)
        # Ensure default values
        if "files_to_modify" not in plan: plan["files_to_modify"] = []
        if "plan" not in plan: plan["plan"] = "No plan details provided"
        if "rationale" not in plan: plan["rationale"] = "No rationale provided"
        if "estimated_lines" not in plan: plan["estimated_lines"] = 0
        return plan
    except: return None

def analyze_failure(code_attempt, error_output):
    """
    CRITIC AGENT: Analyzes why the code failed.
    """
    prompt = f"""
    You are the Senior Reviewer (Critic Agent). 
    A colleague attempted a fix, but the test FAILED with the following error:
    
    --- ERROR ---
    {error_output}
    
    --- ATTEMPTED CODE ---
    {code_attempt}
    
    Analyze briefly (max 3 bullet points):
    1. What is the exact technical cause of the failure? (e.g. undefined variable, reversed logic)
    2. What must change in the next attempt?
    3. Is there a syntax or indentation fault?
    
    Be direct and technical. Start your analysis immediately.
    """
    return ask_llm(prompt)

def generate_patch(file_content, plan, feedback=None, context_snippet=None, critic_advice=None):
    """
    Developer Agent: Generates a patch for the file. 
    Uses SEARCH/REPLACE blocks for large files to ensure high precision without brittle line numbers.
    Includes advice from the Critic to avoid previous errors.
    """
    is_large = len(file_content) > 10000
    critic_str = f"\n### SENIOR REVIEWER ADVICE (CRITIC):\n{critic_advice}\n" if critic_advice else ""
    feedback_str = f"\n### PAST ERRORS TO RECTIFY:\n{feedback}\n" if feedback else ""
    
    # Extra instruction for deep refinement
    persistence_directive = ""
    if feedback and feedback.count("Attempt") >= 3:
        persistence_directive = "\n[bold yellow]WARNING:[/bold yellow] Multiple attempts have failed. Do NOT repeat the same logic. Think out of the box and try a DIFFERENT technical approach to solve the issue once and for all.\n"
    
    # Extra instruction for syntax errors
    syntax_fix_directive = ""
    if (feedback and any(kw in feedback for kw in ["SyntaxError", "IndentationError", "TabError"])) or \
       (critic_advice and "syntax" in critic_advice.lower()):
        syntax_fix_directive = "\nCRITICAL: A syntax/indentation error was detected previously. You MUST ensure all blocks (if/def/class) are closed and indentation is perfectly consistent.\n"

    if is_large:
        prompt = f"""
        You are a Senior Python Developer. Apply a surgical fix to this file.
        {syntax_fix_directive}
        {persistence_directive}
        {critic_str}
        
        GOAL: {plan['plan']}
        {feedback_str}
        
        REQUIRED FORMAT:
        Use ONLY the following XML tags for each change you want to make:
        <search>
        [exact code to replace, including indentation]
        </search>
        <replace>
        [new code]
        </replace>
        
        RULES:
        1. The text inside <search> MUST EXACTLY MATCH a contiguous block of lines in the original file.
        2. Replace ONLY the matched block.
        3. Maintain original indentation.
        4. Do NOT use line numbers. You can use multiple <search>/<replace> blocks if needed.
        
        SNIPPET TO PATCH:
        {context_snippet}
        """
    else:
        prompt = f"""
        You are a Senior Python Developer. Apply a surgical fix to this file.
        {syntax_fix_directive}
        {persistence_directive}
        {critic_str}
        
        GOAL: {plan['plan']}
        {feedback_str}
        
        Return the COMPLETE updated source file inside a triple-backtick python block.
        
        File content:
        ```python
        {file_content}
        ```
        """
    
    response = ask_llm(prompt)
    if not response: return None

    # XML Search/Replace Logic
    if "<search>" in response:
        try:
            import re
            new_code = file_content
            # Extract blocks leniently (ignoring exactly 1 newline at start/end if present)
            blocks = re.findall(r"<search>\n?(.*?)\n?</search>\s*<replace>\n?(.*?)\n?</replace>", response, re.DOTALL)
            for search_text, replace_text in blocks:
                st = search_text
                rt = replace_text
                if st in new_code:
                    new_code = new_code.replace(st, rt)
                else:
                    # Fuzzy match for whitespace/tabs
                    file_lines = new_code.splitlines()
                    search_lines = st.splitlines()
                    matched = False
                    for i in range(len(file_lines) - len(search_lines) + 1):
                        match_count = sum(1 for j in range(len(search_lines)) if file_lines[i+j].strip() == search_lines[j].strip())
                        if len(search_lines) > 0 and match_count / len(search_lines) >= 0.9:
                            indent = file_lines[i][:file_lines[i].find(file_lines[i].strip())] if file_lines[i].strip() else ""
                            indented_rt = "\n".join([(indent + line.strip("\r\n")) if line.strip("\r\n") else "" for line in rt.splitlines()])
                            new_code = "\n".join(file_lines[:i]) + "\n" + indented_rt + "\n" + "\n".join(file_lines[i+len(search_lines):])
                            matched = True
                            break
                    if not matched:
                        return f"FORMAT_[bold red]ERROR:[/bold red] The <search> block '{st[:50]}...' was not found in the original file. Use exact copy-paste!"
            return new_code
        except Exception as e:
            return f"FORMAT_[bold red]ERROR:[/bold red] Parsing of <search>/<replace> tags failed ({e})."
    
    # Standard Full File Return
    if "```python" in response:
        return response.split("```python")[1].split("```")[0].strip()
    elif "```" in response:
        return response.split("```")[1].split("```")[0].strip()
    
    return response.strip()

def generate_test_script(issue_details, file_content, file_path):
    """
    Generates a standalone test script to reproduce the bug and verify the fix.
    """
    prompt = f"""
    Create a standalone Python test script that reproduces the bug described in the issue and verifies that the fix correctly addresses it. 
    The script MUST be self-contained and highly robust.
    
    Issue Title: {issue_details['title']}
    Issue Description: {issue_details['description']}
    
    Target File: {file_path}
    
    REQUIREMENTS:
    1. **Focus on the Fix**: The test should specifically exercise the code path that was modified.
    2. **Logical Verification**: Verify that the actual problematic behavior (e.g. incorrect value, missing event, crash) is gone.
    3. **Robust Imports**: If testing internal modules, use `import sys; sys.path.append('.')`.
    4. **Safe Logic**: Defensive programming against different versions of libraries (e.g. pyqtgraph).
    5. **Exit Codes**: 
       - `sys.exit(0)` if the bug is NOT present (fix works).
       - `sys.exit(1)` if the bug IS present (fix failed).
    
    Return ONLY the Python code in a triple-backtick block.
    """
    
    test_code = ask_llm(prompt)
    if not test_code: return None
    
    if "```python" in test_code:
        test_code = test_code.split("```python")[1].split("```")[0]
    elif "```" in test_code:
        test_code = test_code.split("```")[1].split("```")[0]
        
    return test_code.strip()
