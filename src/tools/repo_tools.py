"""Repository forensic tools - Interim Submission with fixed cloning."""

import tempfile
import subprocess
import os
import ast
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Union

from src.state import Evidence
import logging
logger = logging.getLogger(__name__)


def clone_repository_sandboxed(repo_url: str, full_history: bool = False) -> Union[str, None]:
    """
    Safely clone a git repository to a temporary directory.
    
    Args: 
        repo_url: GitHub URL (https://github.com/user/repo)
        full_history: If True, get full git history (slower). If False, use --depth 1 for speed.
    Returns: Path to cloned repository or None if failed
    """
    temp_dir = tempfile.mkdtemp(prefix="repo_audit_")
    
    try:
        logger.info(f"📥 Cloning {repo_url}...")
        
        # Use --depth 1 for speed, or full history if requested
        clone_cmd = ["git", "clone"]
        if not full_history:
            clone_cmd.extend(["--depth", "1"])
        clone_cmd.extend([repo_url, temp_dir])
        
        result = subprocess.run(
            clone_cmd,
            capture_output=True,
            text=True,
            timeout=1200  # Increased for massive repositories
        )
        
        if result.returncode != 0:
            error_msg = result.stderr[:200] if result.stderr else "Unknown error"
            logger.error(f"❌ Clone failed: {error_msg}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        
        # Add note about history in the rationale later
        if full_history:
            logger.info(f"✅ Cloned successfully with FULL history to {temp_dir}")
        else:
            logger.info(f"✅ Cloned successfully (latest commit only) to {temp_dir}")
            
        return temp_dir
        
    except Exception as e:
        logger.error(f"❌ Clone failed: {str(e)}")
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
        logger.error(f"⚠️ Error getting git history: {e}")
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
        logger.error(f"⚠️ Error finding Python files: {e}")
    
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
    """Analyze overall repository structure and core python modules."""
    try:
        py_files = find_python_files(repo_path)
        
        # Discover major source directories
        top_level_modules = []
        for item in os.listdir(repo_path):
            full_item = os.path.join(repo_path, item)
            if os.path.isdir(full_item) and not item.startswith('.') and item not in ['tests', 'docs', 'examples', 'venv', '__pycache__']:
                # only count if they contain python files or are known patterns (like src, lib)
                if any(f.startswith(item + "/") for f in py_files) or item == 'src':
                    top_level_modules.append(item)
                    
        has_src = 'src' in top_level_modules
        has_tests = os.path.isdir(os.path.join(repo_path, 'tests'))
        
        structure = []
        if top_level_modules:
            structure.append(f"Modules: [{', '.join(top_level_modules)}]")
        if has_tests:
            structure.append("Tests Present")
        structure.append(f"Total Python Files: {len(py_files)}")
        
        rationale = f"Repository architecture confirmed. Core modules identified: {', '.join(top_level_modules)}. System size: {len(py_files)} files."
        if not top_level_modules:
            rationale = f"Atypical architecture. No distinct top-level source modules detected across {len(py_files)} files."
            
        return Evidence(
            goal="Repository Format & Onboarding",
            found=True,
            content=" | ".join(structure),
            location="repository",
            rationale=rationale,
            confidence=0.9 if top_level_modules else 0.6
        )
    except Exception as e:
        return Evidence(
            goal="Repository Format & Onboarding",
            found=False,
            content=str(e),
            location="repository",
            rationale="Failed to recursively analyze repository structure map.",
            confidence=0.0
        )


def get_contributor_stats(repo_path: str) -> Evidence:
    """Analyze contributor frequency using git shortlog."""
    try:
        result = subprocess.run(
            ["git", "shortlog", "-sn", "--all"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        if result.returncode != 0:
            return Evidence(
                goal="Contributor Analysis",
                found=False,
                content=result.stderr,
                location="git shortlog",
                rationale="Failed to get contributor stats",
                confidence=0.0
            )
        
        lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
        if not lines:
            return Evidence(
                goal="Contributor Analysis",
                found=False,
                content=None,
                location="git shortlog",
                rationale="No contributors found or shallow clone limited history",
                confidence=0.5
            )
            
        top_contributors = lines[:5]
        return Evidence(
            goal="Contributor Analysis",
            found=True,
            content="\n".join(top_contributors),
            location="git shortlog",
            rationale=f"Found {len(lines)} contributors. Top ones: {', '.join(top_contributors[:3])}",
            confidence=0.9
        )
    except Exception as e:
        return Evidence(
            goal="Contributor Analysis",
            found=False,
            content=str(e),
            location="git shortlog",
            rationale="Error running contributor analysis",
            confidence=0.0
        )


def detect_license(repo_path: str) -> Evidence:
    """Detect presence of open-source license files."""
    license_files = ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
    found_files = []
    
    for f in license_files:
        if check_file_exists(repo_path, f):
            found_files.append(f)
            
    if found_files:
        return Evidence(
            goal="License Detection",
            found=True,
            content=found_files[0],
            location=found_files[0],
            rationale=f"Found license file: {found_files[0]}",
            confidence=0.9
        )
    return Evidence(
        goal="License Detection",
        found=False,
        content=None,
        location="repository root",
        rationale="No standard license file found",
        confidence=0.8
    )


def detect_ci_presence(repo_path: str) -> Evidence:
    """Detect standard CI/CD configuration files."""
    ci_paths = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".travis.yml", ".circleci/config.yml"]
    found_ci = []
    
    for path in ci_paths:
        full_path = Path(repo_path) / path
        if full_path.exists():
            found_ci.append(path)
            
    if found_ci:
        return Evidence(
            goal="CI/CD Infrastructure",
            found=True,
            content=", ".join(found_ci),
            location=", ".join(found_ci),
            rationale=f"Found CI/CD configurations: {', '.join(found_ci)}",
            confidence=0.9
        )
    return Evidence(
        goal="CI/CD Infrastructure",
        found=False,
        content=None,
        location="repository root",
        rationale="No standard CI/CD configuration files found",
        confidence=0.8
    )


def detect_tests_folder(repo_path: str) -> Evidence:
    """Detect testing infrastructure and quantify test file coverage ratio."""
    py_files = find_python_files(repo_path)
    
    test_files = [f for f in py_files if f.startswith("test_") or f.endswith("_test.py") or "/test_" in f or f.startswith("tests/")]
    src_files = [f for f in py_files if f not in test_files]
    
    test_dirs = [td for td in ["tests", "test", "spec", "tests/"] if (Path(repo_path) / td).is_dir()]
    
    if test_files:
        ratio = len(test_files) / max(len(src_files), 1)
        coverage_desc = "High" if ratio > 0.5 else "Medium" if ratio > 0.2 else "Low"
        
        folders_msg = f" in folders: {', '.join(test_dirs)}" if test_dirs else ""
        
        return Evidence(
            goal="Test Infrastructure",
            found=True,
            content=f"Test files: {len(test_files)} | Source files: {len(src_files)} | Ratio: {ratio:.2f}",
            location="various" + folders_msg,
            rationale=f"Found {len(test_files)} test files{folders_msg}. This represents a {coverage_desc} testing ratio compared to {len(src_files)} standard source files.",
            confidence=0.9
        )
        
    return Evidence(
        goal="Test Infrastructure",
        found=False,
        content="0 test files found",
        location="repository",
        rationale=f"No standard tests directory or explicit test_*.py files discovered among {len(py_files)} total files.",
        confidence=0.8
    )


def scan_secrets(repo_path: str) -> Evidence:
    """Scan python files for basic leaked secrets patterns."""
    import re
    secret_patterns = [
        r"(?i)api_key\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
        r"(?i)password\s*=\s*['\"][a-zA-Z0-9_\-!@#$%]{8,}['\"]",
        r"(?i)secret\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]",
        r"AKIA[0-9A-Z]{16}"  # AWS key pattern
    ]
    py_files = find_python_files(repo_path)
    found_secrets = []
    
    for f in py_files:
        try:
            with open(Path(repo_path) / f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                for pattern in secret_patterns:
                    if re.search(pattern, content):
                        found_secrets.append(f)
                        break
        except Exception:
            pass
            
    if found_secrets:
        return Evidence(
            goal="Secrets Scanning",
            found=True,
            content="\n".join(found_secrets[:3]),
            location="various",
            rationale=f"Potential leaked secrets found in {len(found_secrets)} files (e.g., {found_secrets[0]})",
            confidence=0.8
        )
        
    return Evidence(
        goal="Secrets Scanning",
        found=False,
        content=None,
        location="repository",
        rationale="No obvious hardcoded secrets detected in Python files",
        confidence=0.7
    )


def main_detective_work(repo_url: str, full_history: bool = False) -> List[Evidence]:
    """
    Run all repo detective tools and return evidence list.
    
    This is the MAIN function called by RepoInvestigatorNode.
    """
    evidences = []
    repo_path = None
    
    # STEP 1: Clone the repository
    repo_path = clone_repository_sandboxed(repo_url, full_history=full_history)
    
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
        content="Successfully cloned to temp directory (shallow clone)",
        location=repo_url,
        rationale="Repository cloned successfully for analysis using --depth 1 for performance",
        confidence=0.9
    ))
    
    try:
        # STEP 4: Get git history
        commits = get_git_history(repo_path)
        
        # UPDATED: Git evidence with explanation for shallow clone
        commit_count = len(commits)
        is_shallow = commit_count == 1  # Shallow clones typically have 1 commit
        
        content = f"Found {commit_count} commit{'s' if commit_count != 1 else ''}"
        if is_shallow:
            content += " (shallow clone - latest commit only)"
            
        rationale = f"Repository has {commit_count} commit{'s' if commit_count != 1 else ''}"
        if is_shallow:
            rationale += ". Using --depth 1 for performance (full history not cloned)"
        
        # Confidence: 0.9 for multiple commits, 0.7 for shallow but working, 0.5 if no commits
        if commit_count > 3:
            confidence = 0.9
        elif commit_count > 1:
            confidence = 0.7
        elif commit_count == 1:
            confidence = 0.6  # Shallow clone - technically correct but limited
        else:
            confidence = 0.3
            
        git_evidence = Evidence(
            goal="Git Forensic Analysis",
            found=commit_count > 0,
            content=content,
            location="git log",
            rationale=rationale,
            confidence=confidence
        )
        evidences.append(git_evidence)
        
        # STEP 5: Check for State Management Evidence
        state_related_files = []
        for file in py_files:
            lower_f = file.lower()
            if any(keyword in lower_f for keyword in ["state", "store", "memory", "schema", "types", "checkpoint"]):
                state_related_files.append(file)
                
        has_state = len(state_related_files) > 0
        state_evidence = Evidence(
            goal="State Management Rigor",
            found=has_state,
            content=", ".join(state_related_files[:5]),
            location="various" if has_state else "repository",
            rationale=f"Found {len(state_related_files)} files related to state management/typing (e.g., {state_related_files[0] if state_related_files else 'None'})",
            confidence=0.9 if has_state else 0.5
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
            
        # STEP 9: Advanced Forensics
        evidences.append(get_contributor_stats(repo_path))
        evidences.append(detect_license(repo_path))
        evidences.append(detect_ci_presence(repo_path))
        evidences.append(detect_tests_folder(repo_path))
        evidences.append(scan_secrets(repo_path))
        
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
                logger.info(f"🧹 Cleaned up {repo_path}")
            except Exception as e:
                logger.warning(f"⚠️ Cleanup warning: {e}")
    
    return evidences


# Simple test function
if __name__ == "__main__":
    # Test with a public repo
    test_url = "https://github.com/langchain-ai/langgraph"
    logger.info(f"\n🔍 Testing repo_tools with: {test_url}\n")
    
    results = main_detective_work(test_url)
    
    logger.info("\n📊 RESULTS:")
    for ev in results:
        status = "✅" if ev.found else "❌"
        logger.info(f"{status} {ev.goal}: {ev.rationale} (conf: {ev.confidence})")