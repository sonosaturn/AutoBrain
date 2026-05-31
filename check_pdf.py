import fitz
import sys

file_path = r"C:\Users\Lorenzo\Documents\university_vault\_PDF_Sources\L10 - Network security.pdf"
try:
    doc = fitz.open(file_path)
    toc = doc.get_toc()
    print("PDF TOC:")
    for entry in toc:
        print(entry)
    print(f"\nTotal pages: {len(doc)}")
except Exception as e:
    print(f"Error: {e}")
