import os, csv, json
try:
    import PyPDF2
    import docx
except ImportError:
    pass # Manejado en el bloque try-except de extracción

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
                elif ext == ".json":
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        jd = json.load(f)
                        combined_text += json.dumps(jd, indent=2, ensure_ascii=False)
                else: # Fallback to text
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        combined_text += f.read()
            except Exception as e:
                combined_text += f"\n[ERROR: No se pudo leer el archivo: {e}]\n"
        return combined_text

class LucidImporter:
    @staticmethod
    def import_csv(file_path, model):
        """Maps a Lucidchart CSV flowchart to WorkflowModel nodes."""
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f); rows = list(reader)
        
        id_map = {}; model.nodes = {}
        # 1st Pass: Create Shapes
        for r in rows:
            name = r.get("Name", "").lower()
            if any(k in name for k in ["line", "arrow", "page"]): continue
            
            lucid_id = r.get("Id", "")
            txt = r.get("Text Area 1", "Nodo")
            tid = "askQuestion" if "?" in txt or "decision" in name else "sendMessage"
            
            new_node = WorkflowNode({
                "id": f"lucid_{lucid_id}", "name": txt[:30], "type": tid,
                "data": {"payload": [{"message": {"text": txt}}]}
            })
            model.nodes[new_node.id] = new_node; id_map[lucid_id] = new_node.id
        
        # 2nd Pass: Connections
        for r in rows:
            if "line" in r.get("Name", "").lower():
                src = r.get("Line Source"); dest = r.get("Line Destination")
                if src in id_map and dest in id_map:
                    model.nodes[id_map[dest]].parentId = id_map[src]
        
        # Auto Layout (Optional, will be called by view)
        return model
