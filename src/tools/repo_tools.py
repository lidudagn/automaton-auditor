

import tempfile
import subprocess
import os
import ast
from pathlib import Path
from typing import List, Dict, Optional

from src.state import Evidence


def clone_repository_sandboxed(repo_url: str) -> str:
    """
    Safely clone a git repository to a temporary directory.
    
    Args: repo_url: GitHub URL (https://github.com/user/repo)
    Returns: Path to cloned repository
    """
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="repo_audit_")
    
    try:
        # Clone the repo
        result = subprocess.run(
            ["git", "clone", repo_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            raise Exception(f"Clone failed: {result.stderr}")
        
        print(f"✅ Cloned to {temp_dir}")
        return temp_dir
        
    except Exception as e:
        # Clean up on failure
        import shutil
        shutil.rmtree(temp_dir, ignore_errors=True)
        raise Exception(f"Clone failed: {str(e)}")


def get_git_history(repo_path: str) -> List[Dict[str, str]]:
    """
    Get commit history from cloned repo.
    
    Returns: List of commits with hash and message
    """
    result = subprocess.run(
        ["git", "log", "--oneline", "--reverse"],
        cwd=repo_path,
        capture_output=True,
        text=True
    )
    
    commits = []
    for line in result.stdout.split('\n'):
        if line.strip():
            parts = line.split(' ', 1)
            if len(parts) == 2:
                commits.append({
                    "hash": parts[0],
                    "message": parts[1]
                })
    
    return commits


def check_file_exists(repo_path: str, file_path: str) -> bool:
    """Check if a specific file exists in repo."""
    full_path = Path(repo_path) / file_path
    return full_path.exists()


def find_python_files(repo_path: str) -> List[str]:
    """Find all .py files in repo."""
    py_files = []
    for root, dirs, files in os.walk(repo_path):
        if '.git' in dirs:
            dirs.remove('.git')  # Skip .git folder
        for file in files:
            if file.endswith('.py'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, repo_path)
                py_files.append(rel_path)
    return py_files


def analyze_file_with_ast(repo_path: str, file_path: str) -> Dict:
    """
    Use AST to analyze a Python file.
    
    Returns: Dict with findings
    """
    full_path = Path(repo_path) / file_path
    if not full_path.exists():
        return {"error": "File not found"}
    
    with open(full_path, 'r') as f:
        content = f.read()
    
    try:
        tree = ast.parse(content)
        
        findings = {
            "has_classes": False,
            "has_functions": False,
            "has_imports": False,
            "class_names": [],
            "function_names": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                findings["has_classes"] = True
                findings["class_names"].append(node.name)
            elif isinstance(node, ast.FunctionDef):
                findings["has_functions"] = True
                findings["function_names"].append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                findings["has_imports"] = True
        
        return findings
        
    except SyntaxError:
        return {"error": "Invalid Python syntax"}


def find_stategraph_usage(repo_path: str) -> Evidence:
    """
    Look for StateGraph usage in the codebase.
    
    Returns: Evidence object
    """
    py_files = find_python_files(repo_path)
    found_graphs = []
    
    for file in py_files:
        full_path = Path(repo_path) / file
        with open(full_path, 'r') as f:
            content = f.read()
        
        if 'StateGraph' in content:
            found_graphs.append(file)
    
    return Evidence(
        goal="Graph Orchestration Architecture",
        found=len(found_graphs) > 0,
        content="\n".join(found_graphs) if found_graphs else None,
        location="repository",
        rationale=f"Found StateGraph in {len(found_graphs)} files",
        confidence=0.8 if found_graphs else 0.2
    )


def main_detective_work(repo_url: str) -> List[Evidence]:
    """
    Run all repo detective tools and return evidence list.
    """
    evidences = []
    
    try:
        # Clone repo
        repo_path = clone_repository_sandboxed(repo_url)
        
        # Get git history
        commits = get_git_history(repo_path)
        git_evidence = Evidence(
            goal="Git Forensic Analysis",
            found=len(commits) > 0,
            content=f"Found {len(commits)} commits" if commits else None,
            location="git log",
            rationale=f"Repository has {len(commits)} commits",
            confidence=0.9 if len(commits) > 3 else 0.5
        )
        evidences.append(git_evidence)
        
        # Check for state.py
        has_state = check_file_exists(repo_path, "src/state.py")
        state_evidence = Evidence(
            goal="State Management Rigor",
            found=has_state,
            content=None,
            location="src/state.py",
            rationale="state.py exists" if has_state else "state.py missing",
            confidence=0.9 if has_state else 0.1
        )
        evidences.append(state_evidence)
        
        # Find StateGraph usage
        graph_evidence = find_stategraph_usage(repo_path)
        evidences.append(graph_evidence)
        
        # Clean up
        import shutil
        shutil.rmtree(repo_path, ignore_errors=True)
        
    except Exception as e:
        # Error evidence
        error_evidence = Evidence(
            goal="Repository Access",
            found=False,
            content=str(e),
            location=repo_url,
            rationale="Failed to analyze repo",
            confidence=0.0
        )
        evidences.append(error_evidence)
    
    return evidences