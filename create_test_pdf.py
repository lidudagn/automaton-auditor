# save this as create_test_pdf.py in your root
from fpdf import FPDF
from src.tools.doc_tools import analyze_pdf_report

# 1️⃣ Create the PDF
pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, """# Test Report
We implemented parallel detectives using Fan-Out/Fan-In.
The src/state.py file contains Pydantic models.
The src/graph.py file implements partial graph orchestration.
""")
pdf_file = "test_report.pdf"
pdf.output(pdf_file)
print(f"PDF created: {pdf_file}")

# 2️⃣ Analyze it
results = analyze_pdf_report(pdf_file)
for ev in results:
    print(f"\n{ev.goal}: {'✅' if ev.found else '❌'}")
    print(f"  Content: {ev.content}")
    print(f"  Rationale: {ev.rationale}")
    print(f"  Confidence: {ev.confidence}")