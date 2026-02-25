
import os
import re
from typing import List, Dict, Optional
from pathlib import Path

from src.state import Evidence

# Try to import PDF libraries (handle if not installed)
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("⚠️  pypdf not installed. Run: uv add pypdf")


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text from a PDF file.
    
    Args: pdf_path - Path to PDF file
    Returns: Extracted text as string
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found: {pdf_path}")
    
    if not PYPDF_AVAILABLE:
        # Fallback - just read as text (won't work for PDFs but prevents crash)
        with open(pdf_path, 'r', errors='ignore') as f:
            return f.read()
    
    text = ""
    try:
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text() or ""
                text += f"\n--- Page {page_num + 1} ---\n"
                text += page_text
    except Exception as e:
        text = f"Error extracting PDF: {str(e)}"
    
    return text


def search_keywords(text: str, keywords: List[str]) -> Dict[str, bool]:
    """
    Search for keywords in text.
    
    Returns: Dict of {keyword: found}
    """
    results = {}
    text_lower = text.lower()
    
    for keyword in keywords:
        results[keyword] = keyword.lower() in text_lower
    
    return results


def extract_file_paths(text: str) -> List[str]:
    """
    Extract potential file paths from text.
    Looks for patterns like src/anything.py, tests/anything.py
    """
    # Common Python file patterns
    patterns = [
        r'src/[\w/]+\.py',
        r'tests?/[\w/]+\.py',
        r'[\w/]+/[\w/]+\.py',
    ]
    
    paths = []
    for pattern in patterns:
        found = re.findall(pattern, text)
        paths.extend(found)
    
    # Remove duplicates
    return list(set(paths))


def analyze_pdf_report(pdf_path: str) -> List[Evidence]:
    """
    Main function to analyze PDF and return evidence list.
    """
    evidences = []
    
    try:
        # Extract text
        text = extract_text_from_pdf(pdf_path)
        
        # Evidence 1: Document accessible
        accessible_evidence = Evidence(
            goal="Document Access",
            found=len(text) > 100,  # Has substantial text
            content=f"Extracted {len(text)} characters",
            location=pdf_path,
            rationale="Successfully read PDF file" if len(text) > 100 else "PDF may be empty or unreadable",
            confidence=0.9 if len(text) > 100 else 0.3
        )
        evidences.append(accessible_evidence)
        
        # Evidence 2: Check for key terms
        keywords = [
            "Dialectical Synthesis",
            "Fan-In",
            "Fan-Out",
            "Metacognition",
            "State Synchronization",
            "parallel",
            "detective",
            "judge"
        ]
        
        keyword_results = search_keywords(text, keywords)
        found_keywords = [k for k, v in keyword_results.items() if v]
        
        keyword_evidence = Evidence(
            goal="Theoretical Depth",
            found=len(found_keywords) > 0,
            content=", ".join(found_keywords) if found_keywords else None,
            location=pdf_path,
            rationale=f"Found {len(found_keywords)} relevant keywords",
            confidence=0.7 if len(found_keywords) > 3 else 0.4
        )
        evidences.append(keyword_evidence)
        
        # Evidence 3: Extract file paths mentioned
        paths = extract_file_paths(text)
        
        paths_evidence = Evidence(
            goal="Report File References",
            found=len(paths) > 0,
            content="\n".join(paths[:10]) if paths else None,
            location=pdf_path,
            rationale=f"Found {len(paths)} file path references in document",
            confidence=0.8 if paths else 0.2
        )
        evidences.append(paths_evidence)
        
    except Exception as e:
        error_evidence = Evidence(
            goal="Document Analysis",
            found=False,
            content=str(e),
            location=pdf_path,
            rationale="Failed to analyze PDF",
            confidence=0.0
        )
        evidences.append(error_evidence)
    
    return evidences


# Simple test function
if __name__ == "__main__":
    # Test with a sample file
    test_file = input("Enter path to PDF (or leave blank to skip): ")
    if test_file and os.path.exists(test_file):
        results = analyze_pdf_report(test_file)
        for ev in results:
            print(f"\n{ev.goal}: {'✅' if ev.found else '❌'}")
            print(f"  {ev.rationale}")
    else:
        print("No test file provided. Run with actual PDF later.")