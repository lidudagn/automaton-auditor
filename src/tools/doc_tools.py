"""Document forensic tools - Improved with OCR awareness."""

import os
import re
from typing import List, Dict, Optional
from pathlib import Path

from src.state import Evidence

# Try to import PDF libraries
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

# Optional OCR support
try:
    import pytesseract
    from pdf2image import convert_from_path
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False


def analyze_pdf_intelligently(pdf_path: str) -> Dict[str, any]:
    """
    Intelligently analyze PDF to determine:
    - Has extractable text?
    - Is it image-based?
    - Contains images?
    - Needs OCR?
    """
    result = {
        "has_text": False,
        "text_length": 0,
        "has_images": False,
        "image_count": 0,
        "page_count": 0,
        "is_scanned": False,
        "needs_ocr": False,
        "extracted_text": ""
    }
    
    if not os.path.exists(pdf_path):
        return result
    
    try:
        # Use PyMuPDF for best analysis
        if PYMUPDF_AVAILABLE:
            doc = fitz.open(pdf_path)
            result["page_count"] = len(doc)
            
            # Check for text and images on each page
            total_text = ""
            total_images = 0
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Extract text
                text = page.get_text()
                if text and text.strip():
                    total_text += text + "\n"
                
                # Check for images
                image_list = page.get_images()
                total_images += len(image_list)
            
            result["has_text"] = len(total_text.strip()) > 100
            result["text_length"] = len(total_text)
            result["has_images"] = total_images > 0
            result["image_count"] = total_images
            result["extracted_text"] = total_text
            
            # Determine if scanned (has images but no text)
            if total_images > 0 and not result["has_text"]:
                result["is_scanned"] = True
                result["needs_ocr"] = OCR_AVAILABLE
            
            doc.close()
            
        # Fallback to pypdf
        elif PYPDF_AVAILABLE:
            reader = pypdf.PdfReader(pdf_path)
            result["page_count"] = len(reader.pages)
            
            total_text = ""
            for page in reader.pages:
                text = page.extract_text() or ""
                total_text += text
            
            result["has_text"] = len(total_text.strip()) > 100
            result["text_length"] = len(total_text)
            result["extracted_text"] = total_text
    
    except Exception as e:
        print(f"⚠️ PDF analysis error: {e}")
    
    return result


def extract_text_with_ocr(pdf_path: str) -> str:
    """Extract text using OCR for scanned PDFs."""
    if not OCR_AVAILABLE:
        return "OCR not available"
    
    try:
        images = convert_from_path(pdf_path)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img) + "\n"
        return text
    except Exception as e:
        return f"OCR failed: {str(e)}"


def analyze_pdf_report(pdf_path: str) -> List[Evidence]:
    """
    Main function to analyze PDF and return evidence list.
    Now with intelligent PDF type detection.
    """
    evidences = []
    
    try:
        # First, intelligently analyze PDF
        analysis = analyze_pdf_intelligently(pdf_path)
        
        # Evidence 1: Document accessibility
        if analysis["has_text"]:
            accessible_evidence = Evidence(
                goal="Document Access",
                found=True,
                content=f"Extracted {analysis['text_length']} characters from {analysis['page_count']} pages",
                location=pdf_path,
                rationale="Successfully extracted text from PDF",
                confidence=0.9
            )
        elif analysis["is_scanned"]:
            accessible_evidence = Evidence(
                goal="Document Access",
                found=False,
                content=f"PDF appears to be scanned/image-based with {analysis['image_count']} images. OCR required.",
                location=pdf_path,
                rationale="PDF contains images but no extractable text - may need OCR",
                confidence=0.7
            )
            
            # Try OCR if available
            if OCR_AVAILABLE:
                ocr_text = extract_text_with_ocr(pdf_path)
                if len(ocr_text) > 100:
                    analysis["extracted_text"] = ocr_text
                    analysis["has_text"] = True
                    
        else:
            accessible_evidence = Evidence(
                goal="Document Access",
                found=False,
                content="No extractable text found in PDF",
                location=pdf_path,
                rationale="PDF may be empty, corrupted, or have no text layer",
                confidence=0.3
            )
        
        evidences.append(accessible_evidence)
        
        # Evidence 2: Theoretical depth (if we have text)
        if analysis["has_text"] and analysis["extracted_text"]:
            text = analysis["extracted_text"]
            
            keywords = [
                "Dialectical Synthesis", "Fan-In", "Fan-Out",
                "Metacognition", "State Synchronization",
                "parallel", "detective", "judge", "LangGraph"
            ]
            
            found_keywords = []
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    found_keywords.append(keyword)
            
            keyword_evidence = Evidence(
                goal="Theoretical Depth",
                found=len(found_keywords) > 0,
                content=", ".join(found_keywords) if found_keywords else None,
                location=pdf_path,
                rationale=f"Found {len(found_keywords)} relevant keywords: {', '.join(found_keywords[:3])}" if found_keywords else "No keywords found",
                confidence=0.8 if len(found_keywords) > 3 else 0.5 if found_keywords else 0.2
            )
            evidences.append(keyword_evidence)
            
            # Extract file paths
            paths = re.findall(r'src/[\w/]+\.py', text)
            paths_evidence = Evidence(
                goal="Report File References",
                found=len(paths) > 0,
                content="\n".join(paths[:5]) if paths else None,
                location=pdf_path,
                rationale=f"Found {len(paths)} file path references",
                confidence=0.8 if paths else 0.2
            )
            evidences.append(paths_evidence)
            
        else:
            # No text - explain why
            if analysis["is_scanned"]:
                reason = "PDF appears to be scanned/image-based"
            else:
                reason = "No extractable text content"
            
            no_text_evidence = Evidence(
                goal="Theoretical Depth",
                found=False,
                content=reason,
                location=pdf_path,
                rationale=f"Cannot analyze keywords: {reason}",
                confidence=0.4
            )
            evidences.append(no_text_evidence)
            
            no_paths_evidence = Evidence(
                goal="Report File References",
                found=False,
                content=reason,
                location=pdf_path,
                rationale=f"Cannot extract file paths: {reason}",
                confidence=0.3
            )
            evidences.append(no_paths_evidence)
        
        # Evidence about PDF type (new)
        pdf_type_evidence = Evidence(
            goal="PDF Type Analysis",
            found=True,
            content=f"Pages: {analysis['page_count']}, Has text: {analysis['has_text']}, Has images: {analysis['has_images']}, Scanned: {analysis['is_scanned']}",
            location=pdf_path,
            rationale=f"PDF contains {analysis['page_count']} pages, {'text' if analysis['has_text'] else 'no text'}, {analysis['image_count']} images",
            confidence=0.9
        )
        evidences.append(pdf_type_evidence)
        
    except Exception as e:
        error_evidence = Evidence(
            goal="Document Analysis",
            found=False,
            content=str(e),
            location=pdf_path,
            rationale=f"Failed to analyze PDF: {type(e).__name__}",
            confidence=0.0
        )
        evidences.append(error_evidence)
    
    return evidences