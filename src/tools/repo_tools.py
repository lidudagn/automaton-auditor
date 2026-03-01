"""Repository forensic tools - Phase 4 Master Thinker Edition."""

import tempfile
import subprocess
import os
import ast
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Union
from datetime import datetime

from src.state import Evidence
import logging
logger = logging.getLogger(__name__)


def clone_repository_sandboxed(repo_url: str, full_history: bool = False) -> Union[str, None]:
    """Safely clone a git repository to a temporary directory."""
    temp_dir = tempfile.mkdtemp(prefix="repo_audit_")
    try:
        logger.info(f"📥 Cloning {repo_url}...")
        clone_cmd = ["git", "clone"]
        if not full_history:
            clone_cmd.extend(["--depth", "1"])
        clone_cmd.extend([repo_url, temp_dir])
        
        result = subprocess.run(clone_cmd, capture_output=True, text=True, timeout=1200)
        
        if result.returncode != 0:
            logger.error(f"❌ Clone failed: {result.stderr[:200]}")
            shutil.rmtree(temp_dir, ignore_errors=True)
            return None
        return temp_dir
    except Exception as e:
        logger.error(f"❌ Clone failed: {str(e)}")
        shutil.rmtree(temp_dir, ignore_errors=True)
        return None


def get_git_history(repo_path: str) -> List[Dict[str, str]]:
    """Get commit history from cloned repo."""
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--reverse"],
            cwd=repo_path, capture_output=True, text=True, timeout=30
        )
        commits = []
        for line in result.stdout.split('\n'):
            if line.strip():
                parts = line.split(' ', 1)
                if len(parts) == 2:
                    commits.append({"hash": parts[0], "message": parts[1]})
        return commits
    except Exception as e:
        logger.error(f"⚠️ Error getting git history: {e}")
        return []


def find_python_files(repo_path: str) -> List[str]:
    """Find all .py files in repo."""
    py_files = []
    try:
        for root, dirs, files in os.walk(repo_path):
            if '.git' in dirs: dirs.remove('.git')
            if '__pycache__' in dirs: dirs.remove('__pycache__')
            for file in files:
                if file.endswith('.py'):
                    rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                    py_files.append(rel_path)
    except Exception as e:
        logger.error(f"⚠️ Error finding Python files: {e}")
    return py_files


class OrchestrationVisitor(ast.NodeVisitor):
    """AST visitor to detect LangGraph orchestration patterns."""
    def __init__(self):
        self.nodes = []
        self.edges = []
        self.conditional_edges = []
        self.fan_out_detected = False
        self.fan_in_detected = False
        self.state_graph_instantiated = False

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'StateGraph':
            self.state_graph_instantiated = True
        
        if isinstance(node.func, ast.Attribute):
            if node.func.attr == 'add_node':
                if len(node.args) > 0 and isinstance(node.args[0], ast.Constant):
                    val = node.args[0].value
                    self.nodes.append(val)
            elif node.func.attr == 'add_edge':
                if len(node.args) >= 2:
                    start = None
                    end = None
                    if isinstance(node.args[0], ast.Constant):
                        start = node.args[0].value
                    if isinstance(node.args[1], ast.Constant):
                        end = node.args[1].value
                    if start and end:
                        self.edges.append((start, end))
            elif node.func.attr == 'add_conditional_edges':
                if len(node.args) >= 1:
                    source = None
                    if isinstance(node.args[0], ast.Constant):
                        source = node.args[0].value
                    if source:
                        self.conditional_edges.append(source)
        self.generic_visit(node)

    def analyze(self):
        sources = [e[0] for e in self.edges]
        for s in set(sources):
            if sources.count(s) > 1: self.fan_out_detected = True
        targets = [e[1] for e in self.edges]
        for t in set(targets):
            if targets.count(t) > 1: self.fan_in_detected = True
        if self.conditional_edges: self.fan_out_detected = True


def verify_parallel_orchestration(repo_path: str) -> Evidence:
    """Advanced AST analysis of Graph Orchestration Architecture."""
    py_files = find_python_files(repo_path)
    total_nodes, total_edges = 0, 0
    fan_out, fan_in, instantiated = False, False, False
    found_files = []

    for file in py_files:
        try:
            with open(Path(repo_path) / file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if 'StateGraph' not in content and 'add_node' not in content: continue
            tree = ast.parse(content)
            visitor = OrchestrationVisitor()
            visitor.visit(tree)
            visitor.analyze()
            if visitor.state_graph_instantiated or visitor.nodes:
                instantiated = True
                total_nodes += len(visitor.nodes)
                total_edges += len(visitor.edges)
                if visitor.fan_out_detected: fan_out = True
                if visitor.fan_in_detected: fan_in = True
                found_files.append(file)
        except Exception: continue

    if instantiated:
        status = "Master Thinker" if (fan_out and fan_in) else "Competent"
        rationale = f"Deep AST confirmed {status} orchestration in {', '.join(found_files[:2])}. Detected {total_nodes} nodes and {total_edges} edges. "
        confidence = 1.0 if (fan_out and fan_in) else 0.8 if (fan_out or fan_in) else 0.6
        if fan_out and fan_in: rationale += "Confirmed parallel fan-out/fan-in architecture."
        return Evidence(goal="Graph Orchestration Architecture", found=True, content=f"Nodes: {total_nodes}, Edges: {total_edges}, Parallel: {fan_out and fan_in}", location=" | ".join(found_files[:3]), rationale=rationale, confidence=confidence)
    return Evidence(goal="Graph Orchestration Architecture", found=False, location="repository", rationale="No StateGraph or functional node wiring detected via AST.", confidence=0.2)


def analyze_git_evolution(repo_path: str) -> Evidence:
    """Analyze the evolutionary narrative of the repository."""
    commits = get_git_history(repo_path)
    if not commits:
        return Evidence(goal="Git Evolution Discovery", found=False, location="git log", rationale="No git history found.", confidence=0.5)

    setup_keys = ['init', 'setup', 'environment', 'readme', 'structure']
    tool_keys = ['tool', 'agent', 'detective', 'llm', 'api']
    graph_keys = ['graph', 'workflow', 'orchestration', 'state', 'stategraph']

    messages = [c['message'].lower() for c in commits]
    signals = []
    if any(any(k in m for k in setup_keys) for m in messages): signals.append("Environment Setup")
    if any(any(k in m for k in tool_keys) for m in messages): signals.append("Tool Engineering")
    if any(any(k in m for k in graph_keys) for m in messages): signals.append("Graph Orchestration")

    if len(signals) >= 3:
        status, confidence = "Master Thinker", 1.0
        rationale = "Commit history follows the canonical FDE progression: " + " -> ".join(signals)
    elif len(signals) == 2:
        status, confidence = "Competent Builder", 0.7
        rationale = f"Detected partial progression narrative: {' -> '.join(signals)}"
    else:
        status, confidence = "Generic Developer", 0.4
        rationale = "Git history lacks a clear architectural progression narrative."

    return Evidence(goal="Git Evolution Discovery", found=len(signals) > 0, content=" | ".join(signals), location="git history", rationale=f"[{status}] {rationale}", confidence=confidence)


def analyze_repo_structure(repo_path: str) -> Evidence:
    """Analyze overall repository structure."""
    try:
        py_files = find_python_files(repo_path)
        top_level_modules = [item for item in os.listdir(repo_path) if os.path.isdir(os.path.join(repo_path, item)) and not item.startswith('.') and item not in ['tests', 'docs', 'examples', 'venv', '__pycache__']]
        has_tests = os.path.isdir(os.path.join(repo_path, 'tests'))
        structure = [f"Modules: [{', '.join(top_level_modules)}]", f"Total Python Files: {len(py_files)}"]
        if has_tests: structure.append("Tests Present")
        return Evidence(goal="Repository Format & Onboarding", found=True, content=" | ".join(structure), location="repository", rationale=f"Architecture confirmed ({len(py_files)} files).", confidence=0.9)
    except Exception as e:
        return Evidence(goal="Repository Format & Onboarding", found=False, content=str(e), location="repository", rationale="Failed to analyze structure.", confidence=0.0)


def detect_license(repo_path: str) -> Evidence:
    """Detect license files."""
    for f in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]:
        if (Path(repo_path) / f).exists():
            return Evidence(goal="License Detection", found=True, content=f, location=f, rationale=f"Found license file: {f}", confidence=0.9)
    return Evidence(goal="License Detection", found=False, location="repository root", rationale="No license found", confidence=0.8)


def detect_ci_presence(repo_path: str) -> Evidence:
    """Detect CI/CD files."""
    ci_paths = [".github/workflows", ".gitlab-ci.yml", "Jenkinsfile", ".travis.yml", ".circleci/config.yml"]
    found = [p for p in ci_paths if (Path(repo_path) / p).exists()]
    if found:
        return Evidence(goal="CI/CD Infrastructure", found=True, content=", ".join(found), location=", ".join(found), rationale=f"Found CI: {', '.join(found)}", confidence=0.9)
    return Evidence(goal="CI/CD Infrastructure", found=False, location="repository root", rationale="No CI found", confidence=0.8)


def detect_tests_folder(repo_path: str) -> Evidence:
    """Detect testing infrastructure."""
    py_files = find_python_files(repo_path)
    test_files = [f for f in py_files if f.startswith("test_") or f.endswith("_test.py") or "/test_" in f or f.startswith("tests/")]
    if test_files:
        ratio = len(test_files) / max(len(py_files) - len(test_files), 1)
        return Evidence(goal="Test Infrastructure", found=True, content=f"Ratio: {ratio:.2f}", location="repository", rationale=f"Found {len(test_files)} test files (Ratio: {ratio:.2f}).", confidence=0.9)
    return Evidence(goal="Test Infrastructure", found=False, location="repository", rationale="No tests found.", confidence=0.8)


def scan_secrets(repo_path: str) -> Evidence:
    """Scan for secrets."""
    import re
    patterns = [r"(?i)api_key\s*=\s*['\"][a-zA-Z0-9_\-]{16,}['\"]", r"AKIA[0-9A-Z]{16}"]
    found = []
    for f in find_python_files(repo_path):
        try:
            with open(Path(repo_path) / f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                if any(re.search(p, content) for p in patterns): found.append(f)
        except Exception: pass
    if found: return Evidence(goal="Secrets Scanning", found=True, content=found[0], location=found[0], rationale=f"Potential secrets in {len(found)} files.", confidence=0.8)
    return Evidence(goal="Secrets Scanning", found=False, location="repository", rationale="No secrets detected.", confidence=0.7)


def detect_structured_output_nuance(repo_path: str) -> Evidence:
    """Detect structured output patterns."""
    patterns = {"BaseModel": 0.4, "TypedDict": 0.3, "dataclass": 0.2, "Field": 0.1}
    confidence = 0.0
    found_signals = set()
    for f in find_python_files(repo_path):
        try:
            with open(Path(repo_path) / f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                for p, w in patterns.items():
                    if p in content and p not in found_signals:
                        confidence += w
                        found_signals.add(p)
        except Exception: pass
    confidence = min(1.0, confidence)
    return Evidence(goal="Structured Output Enforcement", found=confidence > 0.3, content=", ".join(found_signals), location="repository", rationale=f"Patterns detected: {', '.join(found_signals)}. Confidence: {confidence:.2f}", confidence=confidence)


def detect_safe_tool_nuance(repo_path: str) -> Evidence:
    """Detect safe tool patterns."""
    patterns = {"@validator": 0.4, "validate_": 0.3, "sanitize": 0.2, "subprocess.run": 0.1}
    confidence = 0.0
    found_signals = set()
    for f in find_python_files(repo_path):
        try:
            with open(Path(repo_path) / f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                for p, w in patterns.items():
                    if p in content and p not in found_signals:
                        confidence += w
                        found_signals.add(p)
        except Exception: pass
    confidence = min(1.0, confidence)
    return Evidence(goal="Safe Tool Engineering", found=confidence > 0.3, content=", ".join(found_signals), location="repository", rationale=f"Patterns detected: {', '.join(found_signals)}. Confidence: {confidence:.2f}", confidence=confidence)


def detect_judicial_nuance(repo_path: str) -> Evidence:
    """Detect judicial reasoning patterns."""
    patterns = {"reasoning_trace": 0.4, "arbitration": 0.3, "variance": 0.2, "weight": 0.1}
    confidence = 0.0
    found_signals = set()
    for f in find_python_files(repo_path):
        try:
            with open(Path(repo_path) / f, 'r', encoding='utf-8', errors='ignore') as file:
                content = file.read()
                for p, w in patterns.items():
                    if p in content and p not in found_signals:
                        confidence += w
                        found_signals.add(p)
        except Exception: pass
    confidence = min(1.0, confidence)
    return Evidence(goal="Judicial Nuance", found=confidence > 0.3, content=", ".join(found_signals), location="repository", rationale=f"Patterns detected: {', '.join(found_signals)}. Confidence: {confidence:.2f}", confidence=confidence)


def main_detective_work(repo_url: str, full_history: bool = False) -> List[Evidence]:
    """Execute all detectors and return evidence."""
    evidences = []
    repo_path = clone_repository_sandboxed(repo_url, full_history=full_history)
    if not repo_path:
        evidences.append(Evidence(goal="Repository Access", found=False, content=f"Failed to clone: {repo_url}", location=repo_url, rationale="Clone failed.", confidence=0.0))
        return evidences
    
    evidences.append(Evidence(goal="Repository Access", found=True, content="Cloned", location=repo_url, rationale="Cloned successfully.", confidence=0.9))
    
    try:
        evidences.append(analyze_git_evolution(repo_path))
        evidences.append(verify_parallel_orchestration(repo_path))
        evidences.append(analyze_repo_structure(repo_path))
        evidences.append(detect_license(repo_path))
        evidences.append(detect_ci_presence(repo_path))
        evidences.append(detect_tests_folder(repo_path))
        evidences.append(scan_secrets(repo_path))
        evidences.append(detect_structured_output_nuance(repo_path))
        evidences.append(detect_safe_tool_nuance(repo_path))
        evidences.append(detect_judicial_nuance(repo_path))
    except Exception as e:
        logger.error(f"Error: {e}")
        evidences.append(Evidence(goal="Repository Analysis", found=False, content=str(e), location=repo_url, rationale=f"Error: {e}", confidence=0.0))
    finally:
        if repo_path: shutil.rmtree(repo_path, ignore_errors=True)
    return evidences


if __name__ == "__main__":
    test_url = "https://github.com/langchain-ai/langgraph"
    results = main_detective_work(test_url)
    for ev in results:
        logger.info(f"{ev.goal}: {ev.rationale}")