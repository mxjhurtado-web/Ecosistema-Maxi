import docx
import PyPDF2
import os

class DocParser:
    @staticmethod
    def extract_text(file_paths):
        """Extracts text from a list of file paths (.docx, .pdf, .txt)."""
        combined_text = ""
        for path in file_paths:
            filename = os.path.basename(path)
            ext = os.path.splitext(path)[1].lower()
            combined_text += f"\n--- CONTENIDO DE: {filename} ---\n"
            try:
                if ext == ".docx":
                    doc = docx.Document(path)
                    combined_text += "\n".join([p.text for p in doc.paragraphs])
                elif ext == ".pdf":
                    content = []
                    with open(path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        for page in reader.pages:
                            content.append(page.extract_text())
                    combined_text += "\n".join(content)
                else: # Fallback to text
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        combined_text += f.read()
            except Exception as e:
                combined_text += f"\n[ERROR: No se pudo leer el archivo: {e}]\n"
        return combined_text
