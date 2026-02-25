

import os
from src.tools.doc_tools import analyze_pdf_report

def test_pdf(pdf_path):
    print(f"\n{'='*60}")
    print(f"Testing: {pdf_path}")
    print('='*60)
    
    if not os.path.exists(pdf_path):
        print(f"❌ File not found: {pdf_path}")
        return
    
    results = analyze_pdf_report(pdf_path)
    
    for ev in results:
        status = "✅" if ev.found else "❌"
        print(f"\n{status} {ev.goal}")
        print(f"   Location: {ev.location}")
        print(f"   Rationale: {ev.rationale}")
        print(f"   Confidence: {ev.confidence*100:.1f}%")
        if ev.content:
            print(f"   Content: {ev.content[:100]}..." if len(ev.content) > 100 else f"   Content: {ev.content}")

# Test with your existing PDFs
if os.path.exists("test_comprehensive.pdf"):
    test_pdf("test_comprehensive.pdf")
else:
    print("\n⚠️  test_comprehensive.pdf not found")

if os.path.exists("test_with_diagram.pdf"):
    test_pdf("test_with_diagram.pdf")
else:
    print("\n⚠️  test_with_diagram.pdf not found")

if os.path.exists("test_report.pdf"):
    test_pdf("test_report.pdf")
else:
    print("\n⚠️  test_report.pdf not found")

print("\n✅ Test complete")
