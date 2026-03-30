import os
import subprocess
import os.path

def run_tests(modified_file_path, python_exe="python"):
    """
    1. Executes py_compile (Syntax Check).
    2. Executes targeted pytest if the syntax check passes.
    Returns (success, message).
    """
    if not modified_file_path or not os.path.exists(modified_file_path):
        return False, "Missing file path for verification."

    # 1. Syntax Check (Priority 1)
    print(f"[Tester] Syntax check: {modified_file_path}")
    syntax_result = subprocess.run([python_exe, "-m", "py_compile", modified_file_path], capture_output=True, text=True)
    
    if syntax_result.returncode != 0:
        error_msg = syntax_result.stderr
        print(f"Syntax check failed:\n{error_msg}")
        return False, error_msg

    print("Syntax check (py_compile) passed.")

    # 2. Targeted Pytest (Priority 2)
    # Execute pytest only in the modified file directory to be fast and targeted
    target_dir = os.path.dirname(modified_file_path)
    if not target_dir: target_dir = "."
    
    print(f"Attempting targeted pytest in {target_dir}...")
    result = subprocess.run([python_exe, "-m", "pytest", target_dir], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("Targeted tests completed successfully.")
        return True, "Success (Syntax & Targeted Tests OK)"
    else:
        # If pytest fails, we might not have tests, or it could be a real error.
        # Return True if it is just 'no tests collected' (pytest return code 5)
        if result.returncode == 5:
            print("No tests found in target directory. Proceeding with syntax only.")
            return True, "Syntax OK (No tests found)"
        
        print(f"Targeted pytest failed (code {result.returncode}).")
        return False, result.stderr
