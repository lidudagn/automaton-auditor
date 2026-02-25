
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Optional, Any
import hashlib

from src.state import Evidence

# Try to import PDF image extraction
try:
    import pypdf
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False
    print("⚠️ pypdf not fully available")

try:
    import fitz  # PyMuPDF - better for images
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    print("⚠️ fitz/PyMuPDF not installed. Run: uv add PyMuPDF")

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL not installed. Run: uv add pillow")


def extract_images_with_pymupdf(pdf_path: str, output_dir: str) -> List[str]:
    """
    Extract images from PDF using PyMuPDF (best method).
    
    Returns: List of paths to extracted images
    """
    if not PYMUPDF_AVAILABLE:
        return []
    
    try:
        import fitz
        doc = fitz.open(pdf_path)
        image_paths = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                if pix.n - pix.alpha < 4:  # Can save as PNG
                    img_path = os.path.join(output_dir, f"page{page_num+1}_img{img_index+1}.png")
                    pix.save(img_path)
                    image_paths.append(img_path)
                else:  # Convert to PNG
                    pix1 = fitz.Pixmap(fitz.csRGB, pix)
                    img_path = os.path.join(output_dir, f"page{page_num+1}_img{img_index+1}.png")
                    pix1.save(img_path)
                    pix1 = None
                pix = None
        
        doc.close()
        return image_paths
    
    except Exception as e:
        print(f"⚠️ PyMuPDF extraction error: {e}")
        return []


def extract_images_with_pypdf(pdf_path: str, output_dir: str) -> List[str]:
    """
    Basic image detection using pypdf (limited).
    """
    if not PYPDF_AVAILABLE:
        return []
    
    try:
        reader = PdfReader(pdf_path)
        image_paths = []
        
        for page_num, page in enumerate(reader.pages):
            if '/XObject' in page['/Resources']:
                xObject = page['/Resources']['/XObject'].get_object()
                for obj_name in xObject:
                    obj = xObject[obj_name]
                    if obj['/Subtype'] == '/Image':
                        # We found an image but can't easily extract
                        # Just note it exists
                        img_path = os.path.join(output_dir, f"page{page_num+1}_image_found.txt")
                        with open(img_path, 'w') as f:
                            f.write(f"Image detected on page {page_num+1}")
                        image_paths.append(img_path)
        
        return image_paths
    
    except Exception as e:
        print(f"⚠️ PyPDF image detection error: {e}")
        return []


def analyze_image_with_heuristics(image_path: str) -> Dict[str, Any]:
    """
    Analyze image to determine if it's a diagram/flowchart.
    Uses basic heuristics (size, dimensions, etc.)
    """
    if not PIL_AVAILABLE or not os.path.exists(image_path):
        return {"is_diagram": False, "confidence": 0.0}
    
    try:
        from PIL import Image
        img = Image.open(image_path)
        
        # Basic heuristics
        width, height = img.size
        aspect_ratio = width / height if height > 0 else 0
        file_size = os.path.getsize(image_path)
        
        # Diagrams often have:
        # - Moderate size (not too small, not huge)
        # - Text-like elements (detect via image mode)
        # - Reasonable aspect ratio
        
        is_likely_diagram = (
            300 < width < 2000 and
            200 < height < 2000 and
            0.5 < aspect_ratio < 2.0 and
            file_size > 10000  # At least 10KB
        )
        
        # Count colors (simplified)
        img = img.convert('RGB')
        colors = img.getcolors(maxcolors=256)
        has_few_colors = colors is not None and len(colors) < 50  # Diagrams often have limited colors
        
        confidence = 0.0
        if is_likely_diagram and has_few_colors:
            confidence = 0.8
        elif is_likely_diagram:
            confidence = 0.5
        
        return {
            "is_diagram": confidence > 0.5,
            "confidence": confidence,
            "width": width,
            "height": height,
            "aspect_ratio": aspect_ratio,
            "file_size": file_size,
            "has_few_colors": has_few_colors
        }
    
    except Exception as e:
        return {"is_diagram": False, "confidence": 0.0, "error": str(e)}


def detect_diagrams_in_pdf(pdf_path: str) -> List[Evidence]:
    """
    Main function to detect diagrams in PDF.
    
    Returns: List of Evidence objects about diagrams found.
    """
    evidences = []
    
    if not os.path.exists(pdf_path):
        evidences.append(Evidence(
            goal="Diagram Analysis",
            found=False,
            content="PDF file not found",
            location=pdf_path,
            rationale="Cannot analyze missing PDF",
            confidence=0.0
        ))
        return evidences
    
    # Create temp dir for extracted images
    with tempfile.TemporaryDirectory(prefix="vision_audit_") as temp_dir:
        
        # Try PyMuPDF first (best)
        images = extract_images_with_pymupdf(pdf_path, temp_dir)
        
        # Fallback to pypdf if no images found
        if not images:
            images = extract_images_with_pypdf(pdf_path, temp_dir)
        
        if not images:
            # No images found
            evidences.append(Evidence(
                goal="Diagram Analysis",
                found=False,
                content="No images detected in PDF",
                location=pdf_path,
                rationale="PDF appears to contain no embedded images",
                confidence=0.7  # Pretty confident there are no images
            ))
            return evidences
        
        # We found images - analyze them
        diagram_count = 0
        diagram_details = []
        
        for img_path in images:
            analysis = analyze_image_with_heuristics(img_path)
            if analysis.get("is_diagram", False):
                diagram_count += 1
                diagram_details.append({
                    "path": os.path.basename(img_path),
                    "confidence": analysis.get("confidence", 0),
                    "size": f"{analysis.get('width', 0)}x{analysis.get('height', 0)}"
                })
        
        if diagram_count > 0:
            evidences.append(Evidence(
                goal="Diagram Analysis",
                found=True,
                content=f"Found {diagram_count} potential diagrams:\n" + "\n".join([
                    f"  - {d['path']} ({d['size']}) conf: {d['confidence']:.1%}"
                    for d in diagram_details
                ]),
                location=pdf_path,
                rationale=f"Detected {diagram_count} images that appear to be diagrams/flowcharts",
                confidence=0.8
            ))
        else:
            evidences.append(Evidence(
                goal="Diagram Analysis",
                found=False,
                content=f"Found {len(images)} images but none appear to be diagrams",
                location=pdf_path,
                rationale="Images detected but they don't match diagram heuristics",
                confidence=0.6
            ))
    
    return evidences


# Simple test
if __name__ == "__main__":
    test_pdf = input("Enter PDF path to test: ")
    if os.path.exists(test_pdf):
        results = detect_diagrams_in_pdf(test_pdf)
        for ev in results:
            print(f"\n{ev.goal}: {'✅' if ev.found else '❌'}")
            print(f"  {ev.rationale}")
            if ev.content:
                print(f"  Details:\n{ev.content}")
    else:
        print("No test PDF provided")