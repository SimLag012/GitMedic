import os
import subprocess
import shutil
from llm import generate_test_script
from tester import run_tests

class VerifierAgent:
    def _setup_venv(self, work_dir):
        """
        Creates a virtual environment in the working directory and returns the python executable path.
        """
        import venv
        import sys
        
        venv_dir = os.path.join(work_dir, ".gitfix_venv")
        if not os.path.exists(venv_dir):
            print(f"[VerifierAgent] Creating venv in {venv_dir}...")
            venv.create(venv_dir, with_pip=True)
            
        # Path of the python executable in the venv (Windows vs Unix)
        if sys.platform == "win32":
            python_exe = os.path.normpath(os.path.join(venv_dir, "Scripts", "python.exe"))
        else:
            python_exe = os.path.normpath(os.path.join(venv_dir, "bin", "python"))
            
        if not os.path.exists(python_exe):
            print(f"[VerifierAgent] WARNING: python_exe not found in {python_exe}. Recreating venv...")
            shutil.rmtree(venv_dir, ignore_errors=True)
            venv.create(venv_dir, with_pip=True)
            
        return python_exe

    def _run_with_dep_fix(self, python_exe, command_args, max_retries=3):
        """
        Executes a command and attempts to install missing dependencies if it fails with ModuleNotFoundError.
        """
        import os
        env = os.environ.copy()
        # Add the current directory to PYTHONPATH for local modules
        env["PYTHONPATH"] = "." + os.pathsep + env.get("PYTHONPATH", "")
        
        for i in range(max_retries):
            res = subprocess.run([python_exe] + command_args, capture_output=True, text=True, env=env)
            if res.returncode == 0:
                return res
            
            # Look for "ModuleNotFoundError: No module named '...'"
            import re
            match = re.search(r"ModuleNotFoundError: No module named '([^']+)'", res.stderr)
            
            # Special case for pyqtgraph: requires PyQt5/6 or PySide2/6
            if "PyQtGraph requires one of PyQt5, PyQt6, PySide2 or PySide6" in res.stderr:
                missing_mod = "PyQt5"
                print(f"[VerifierAgent] Qt dependencies error detected for pyqtgraph. Selecting {missing_mod}...")
            elif match:
                missing_mod = match.group(1).split('.')[0] # Root module only
                
                # List of common local directory names to NOT install via pip
                local_dirs = ["app", "src", "tests", "test", "services", "utils", "core", "api"]
                if missing_mod.lower() in local_dirs:
                    print(f"[VerifierAgent] Local module '{missing_mod}' not present. This might be a test structure error.")
                    missing_mod = None
                else:
                    print(f"[VerifierAgent] Missing dependency detected: {missing_mod}. Attempting installation...")
            else:
                missing_mod = None
                
            if missing_mod:
                # Common mapping for module names vs pip packages
                pkg_map = {
                    "cv2": "opencv-python", 
                    "PyQt5": "PyQt5", 
                    "numpy": "numpy",
                    "pg": "pyqtgraph",
                    "PIL": "Pillow",
                    "sklearn": "scikit-learn",
                    "yaml": "pyyaml"
                }
                if missing_mod in pkg_map:
                    pkg_to_install = pkg_map[missing_mod]
                else:
                    pkg_to_install = missing_mod
                    
                install_res = subprocess.run([python_exe, "-m", "pip", "install", pkg_to_install], capture_output=True)
                if install_res.returncode != 0:
                    print(f"[VerifierAgent] Failed installation of {pkg_to_install}.")
                    return res
                print(f"[VerifierAgent] Installed {pkg_to_install}. Retrying test ({i+1}/{max_retries})...")
            else:
                # Another type of error, we stop the dep fix loop
                return res
        return res

    def verify(self, execution_data, issue):
        """
        Runs existing tests or generates a new one if missing, fully isolated in venv with auto-dep-fix.
        Returns (success, error_msg).
        """
        print("[VerifierAgent] Starting verification cycle (Isolated in Venv + Smart Dep Fix)...")
        if not execution_data or not execution_data["modified_files"]:
            return False, "No modified files to verify."
            
        original_dir = os.getcwd()
        work_dir = execution_data["work_dir"]
        os.chdir(work_dir)
        
        try:
            python_exe = self._setup_venv(work_dir)
            
            # Skip dependency install if venv was already there
            setup_done_marker = os.path.join(work_dir, ".gitfix_venv_ready")
            
            if not os.path.exists(setup_done_marker):
                print("[VerifierAgent] Preparing environment (Full Setup)...")
                subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], capture_output=True)
                subprocess.run([python_exe, "-m", "pip", "install", "pytest"], capture_output=True)
                
                print("[VerifierAgent] Installing core dependencies: numpy, PyQt5...")
                subprocess.run([python_exe, "-m", "pip", "install", "numpy", "PyQt5"], capture_output=True)
                
                req_file = os.path.join(work_dir, "requirements.txt")
                if os.path.exists(req_file):
                    print(f"[VerifierAgent] Installing requirements...")
                    subprocess.run([python_exe, "-m", "pip", "install", "-r", req_file], capture_output=True)
                
                if os.path.exists(os.path.join(work_dir, "setup.py")) or os.path.exists(os.path.join(work_dir, "pyproject.toml")):
                    print(f"[VerifierAgent] Setup file found. Executing 'pip install -e .'...")
                    subprocess.run([python_exe, "-m", "pip", "install", "-e", "."], cwd=work_dir, capture_output=True)
                
                # Mark as ready
                with open(setup_done_marker, "w") as f: f.write("ok")
                print(f"[VerifierAgent] Environment ready.")
            else:
                print(f"[VerifierAgent] Using existing environment (Persistent).")
            
            main_file = execution_data["modified_files"][0]
            rel_path = os.path.relpath(main_file, start=os.getcwd())
            
            # 1. Syntax Check & Targeted Pytest (Fastest check first)
            print(f"[VerifierAgent] Executing preliminary verifications (Syntax + Targeted Pytest) on {rel_path}...")
            success, message = run_tests(rel_path, python_exe=python_exe)
            if not success:
                print(f"[VerifierAgent] Preliminary verifications failed: {message}")
                return False, message
            
            print(f"[VerifierAgent] Preliminary verifications passed ({message}).")

            # 2. Generate and run automatic test for logic validation
            print("[VerifierAgent] Attempting to generate targeted automatic test for logical bug validation...")
            
            with open(rel_path, "r", encoding='utf-8') as f:
                content = f.read()
            
            test_code = generate_test_script(issue, content, rel_path)
            if test_code:
                test_file = "gitfix_verify_test.py"
                with open(test_file, "w", encoding='utf-8') as f:
                    f.write(test_code)
                
                print(f"[VerifierAgent] Executing generated LOGIC TEST: {test_file}")
                res = self._run_with_dep_fix(python_exe, [test_file])
                
                if res.returncode == 0:
                    print("[VerifierAgent] LOGIC TEST PASSED: The bug appears resolved.")
                    return True, "Logic test passed"
                else:
                    err_msg = res.stderr
                    
                    # Guardrail: If generated test crashes for internal structural errors
                    # But we remain rigorous: if the logical test fails fundamentally, plan might be fragile.
                    if any(err in err_msg for err in ["SyntaxError:", "ModuleNotFoundError:", "ImportError:", "NameError:"]):
                        print(f"[VerifierAgent] STRUCTURAL ERROR in generated test:\n{err_msg[:400]}")
                        return False, f"Structural error in generated test: {err_msg[:200]}"
                        
                    print(f"[VerifierAgent] LOGIC TEST FAILED: The modification does not resolve the specific bug.\n{err_msg}")
                    return False, f"Logic test failed: {err_msg}"
            else:
                print("[VerifierAgent] WARNING: Unable to generate logic test. Relying solely on syntactic correctness.")
                return True, "Syntax OK but no logic test possible."
        except Exception as e:
            return False, str(e)
        finally:
            os.chdir(original_dir)
