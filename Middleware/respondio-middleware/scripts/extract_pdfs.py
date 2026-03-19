import os
from pypdf import PdfReader

DOCS_DIR = r"c:\Users\User\Ecosistema-Maxi\Middleware\respondio-middleware\docs\Documentos_PDF"
OUTPUT_FILE = r"c:\Users\User\Ecosistema-Maxi\Middleware\respondio-middleware\docs\extracted_docs_summary.txt"

def extract_text_from_pdfs():
    if not os.path.exists(DOCS_DIR):
        print(f"Error: Directory {DOCS_DIR} not found.")
        return

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for filename in os.listdir(DOCS_DIR):
            if filename.endswith(".pdf"):
                file_path = os.path.join(DOCS_DIR, filename)
                print(f"Extracting text from: {filename}")
                f.write(f"\n{'='*50}\n")
                f.write(f"FILE: {filename}\n")
                f.write(f"{'='*50}\n\n")
                
                try:
                    reader = PdfReader(file_path)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            f.write(text + "\n")
                except Exception as e:
                    f.write(f"ERROR extracting from {filename}: {str(e)}\n")
                
                f.write("\n\n")

    print(f"Extraction complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_text_from_pdfs()
