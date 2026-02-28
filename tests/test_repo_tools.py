import tempfile
import os
import shutil
from pathlib import Path
import pytest

from src.tools.repo_tools import (
    detect_license,
    detect_ci_presence,
    detect_tests_folder,
    scan_secrets
)

@pytest.fixture
def mock_repo():
    # Create a temporary directory mimicking a repo
    temp_dir = tempfile.mkdtemp(prefix="test_repo_")
    
    # Create CI file
    os.makedirs(os.path.join(temp_dir, ".github", "workflows"), exist_ok=True)
    with open(os.path.join(temp_dir, ".github", "workflows", "test.yml"), "w") as f:
        f.write("name: test")
        
    # Create license file
    with open(os.path.join(temp_dir, "LICENSE.md"), "w") as f:
        f.write("MIT License")
        
    # Create test directory
    os.makedirs(os.path.join(temp_dir, "tests"), exist_ok=True)
    with open(os.path.join(temp_dir, "tests", "test_foo.py"), "w") as f:
        f.write("def test_foo(): pass")
        
    # Create a secret in a file
    with open(os.path.join(temp_dir, "main.py"), "w") as f:
        f.write('api_key = "abcdefghijklmnopqrstuvwxyz"\n')
        
    yield temp_dir
    
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_detect_license(mock_repo):
    ev = detect_license(mock_repo)
    assert ev.found is True
    assert ev.goal == "License Detection"
    assert ev.content == "LICENSE.md"

def test_detect_ci_presence(mock_repo):
    ev = detect_ci_presence(mock_repo)
    assert ev.found is True
    assert ev.goal == "CI/CD Infrastructure"
    assert ".github/workflows" in ev.content

def test_detect_tests_folder(mock_repo):
    ev = detect_tests_folder(mock_repo)
    assert ev.found is True
    assert ev.goal == "Test Infrastructure"
    assert "Test files:" in ev.content
    assert "Ratio:" in ev.content

def test_scan_secrets(mock_repo):
    ev = scan_secrets(mock_repo)
    assert ev.found is True
    assert ev.goal == "Secrets Scanning"
    assert "main.py" in ev.content
