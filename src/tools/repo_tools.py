"""Repository forensic tools - Interim Submission with fixed cloning."""

import tempfile
import subprocess
import os
import ast
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Union

from src.state import Evidence


def clone_repository_sandboxed(repo_url: str) -> Union[str, None]:
    """
    Safely clone a git repository to a temporary directory.
    
    Args: repo_url: GitHub URL (https://github.com/user/repo)
    Returns: Path to cloned repository or None if failed
    """
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="repo_audit_")
    
    try:
        print(f"📥 Cloning {repo_url}...")
        
        # Use --depth 1 for faster clone (only latest commit)
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, temp_dir],
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode != 0:
            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
            print(f"❌ Clone failed: {error_msg}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        
        print(f"✅ Cloned successfully to {temp_dir}")
        return temp_dir
        
    except subprocess.TimeoutExpired:
        print("❌ Clone timed out after 60 seconds")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None
    except Exception as e:
        print(f"❌ Clone failed: {str(e)}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def get_git_history(repo_path: str) -> List[Dict[str, str]]:
    """
    Get commit history from cloned repo.
    
    Returns: List of commits with hash and message
    """
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--reverse"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
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
    except Exception as e:
        print(f"⚠️ Error getting git history: {e}")
        return []


def check_file_exists(repo_path: str, file_path: str) -> bool:
    """Check if a specific file exists in repo."""
    full_path = Path(repo_path) / file_path
    return full_path.exists()


def find_python_files(repo_path: str) -> List[str]:
    """Find all .py files in repo."""
    py_files = []
    try:
        for root, dirs, files in os.walk(repo_path):
            if '.git' in dirs:
                dirs.remove('.git')  # Skip .git folder
            if '__pycache__' in dirs:
                dirs.remove('__pycache__')  # Skip cache
                
            for file in files:
                if file.endswith('.py'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, repo_path)
                    py_files.append(rel_path)
    except Exception as e:
        print(f"⚠️ Error finding Python files: {e}")
    
    return py_files


def analyze_file_with_ast(repo_path: str, file_path: str) -> Dict:
    """
    Use AST to analyze a Python file.
    
    Returns: Dict with findings
    """
    full_path = Path(repo_path) / file_path
    if not full_path.exists():
        return {"error": "File not found"}
    
    try:
        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        tree = ast.parse(content)
        
        findings = {
            "has_classes": False,
            "has_functions": False,
            "has_imports": False,
            "class_names": [],
            "function_names": [],
            "imports": []
        }
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                findings["has_classes"] = True
                findings["class_names"].append(node.name)
            elif isinstance(node, ast.FunctionDef):
                findings["has_functions"] = True
                findings["function_names"].append(node.name)
            elif isinstance(node, ast.Import):
                findings["has_imports"] = True
                for alias in node.names:
                    findings["imports"].append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                findings["has_imports"] = True
                module = node.module or ""
                for alias in node.names:
                    findings["imports"].append(f"{module}.{alias.name}")
        
        return findings
        
    except SyntaxError as e:
        return {"error": f"Invalid Python syntax: {str(e)}"}
    except Exception as e:
        return {"error": f"Analysis failed: {str(e)}"}


def find_stategraph_usage(repo_path: str) -> Evidence:
    """
    Look for StateGraph usage in the codebase.
    
    Returns: Evidence object
    """
    py_files = find_python_files(repo_path)
    found_graphs = []
    
    for file in py_files:
        try:
            full_path = Path(repo_path) / file
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            if 'StateGraph' in content or 'StateGraph' in content:
                found_graphs.append(file)
        except Exception:
            continue  # Skip files that can't be read
    
    if found_graphs:
        return Evidence(
            goal="Graph Orchestration Architecture",
            found=True,
            content="\n".join(found_graphs[:5]),  # First 5 files
            location="repository",
            rationale=f"Found StateGraph in {len(found_graphs)} files: {', '.join(found_graphs[:3])}",
            confidence=0.9
        )
    else:
        return Evidence(
            goal="Graph Orchestration Architecture",
            found=False,
            content=None,
            location="repository",
            rationale="No StateGraph usage detected",
            confidence=0.2
        )


def analyze_repo_structure(repo_path: str) -> Evidence:
    """Analyze overall repository structure."""
    try:
        # Count Python files
        py_files = find_python_files(repo_path)
        
        # Check for common directories
        has_src = os.path.isdir(os.path.join(repo_path, 'src'))
        has_tests = os.path.isdir(os.path.join(repo_path, 'tests'))
        
        structure = []
        if has_src:
            structure.append("src/")
        if has_tests:
            structure.append("tests/")
        structure.append(f"{len(py_files)} Python files")
        
        return Evidence(
            goal="Repository Structure",
            found=True,
            content=", ".join(structure),
            location="repository",
            rationale=f"Found {len(py_files)} Python files" + (" with src/" if has_src else ""),
            confidence=0.8
        )
    except Exception as e:
        return Evidence(
            goal="Repository Structure",
            found=False,
            content=str(e),
            location="repository",
            rationale="Failed to analyze structure",
            confidence=0.0
        )


def main_detective_work(repo_url: str) -> List[Evidence]:
    """
    Run all repo detective tools and return evidence list.
    
    This is the MAIN function called by RepoInvestigatorNode.
    """
    evidences = []
    repo_path = None
    
    # STEP 1: Clone the repository
    repo_path = clone_repository_sandboxed(repo_url)
    
    # STEP 2: Handle clone failure
    if not repo_path:
        evidences.append(Evidence(
            goal="Repository Access",
            found=False,
            content=f"Failed to clone: {repo_url}",
            location=repo_url,
            rationale="Could not clone repository - check URL or network",
            confidence=0.0
        ))
        return evidences
    
    # STEP 3: Clone succeeded - add success evidence
    evidences.append(Evidence(
        goal="Repository Access",
        found=True,
        content=f"Successfully cloned to temp directory",
        location=repo_url,
        rationale="Repository cloned successfully for analysis",
        confidence=0.9
    ))
    
    try:
        # STEP 4: Get git history
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
        
        # STEP 5: Check for state.py
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
        
        # STEP 6: Find StateGraph usage
        graph_evidence = find_stategraph_usage(repo_path)
        evidences.append(graph_evidence)
        
        # STEP 7: Analyze repo structure
        structure_evidence = analyze_repo_structure(repo_path)
        evidences.append(structure_evidence)
        
        # STEP 8: Look for Python files count
        py_files = find_python_files(repo_path)
        if py_files:
            py_evidence = Evidence(
                goal="Python Files Present",
                found=True,
                content=f"Found {len(py_files)} Python files",
                location="repository",
                rationale=f"Repository contains {len(py_files)} .py files",
                confidence=0.9
            )
            evidences.append(py_evidence)
        
    except Exception as e:
        # Catch any unexpected errors during analysis
        error_evidence = Evidence(
            goal="Repository Analysis",
            found=False,
            content=str(e),
            location=repo_url,
            rationale=f"Analysis error: {type(e).__name__}",
            confidence=0.0
        )
        evidences.append(error_evidence)
    
    finally:
        # STEP 9: Always clean up temp directory
        if repo_path and os.path.exists(repo_path):
            try:
                shutil.rmtree(repo_path, ignore_errors=True)
                print(f"🧹 Cleaned up {repo_path}")
            except Exception as e:
                print(f"⚠️ Cleanup warning: {e}")
    
    return evidences


# Simple test function
if __name__ == "__main__":
    # Test with a public repo
    test_url = "https://github.com/langchain-ai/langgraph"
    print(f"\n🔍 Testing repo_tools with: {test_url}\n")
    
    results = main_detective_work(test_url)
    
    print("\n📊 RESULTS:")
    for ev in results:
        status = "✅" if ev.found else "❌"
        print(f"{status} {ev.goal}: {ev.rationale} (conf: {ev.confidence})")