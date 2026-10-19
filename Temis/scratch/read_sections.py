import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Plan_Tecnico_Desacoplamiento_Gobernanza_TEMIS_AppSheet_v1.0.docx'
doc = docx.Document(fp)

capture = False
for p in doc.paragraphs:
    txt = p.text.strip()
    if p.style.name == 'Heading 1' and ('2. Frontera funcional' in txt or '1. Resumen' in txt or '3. Arquitectura' in txt or '5. Matriz' in txt or '10. Backlog' in txt):
        capture = True
        print(f"\n========================================\n{txt}\n========================================")
    elif p.style.name == 'Heading 1' and capture and ('4. Plan' in txt or '6. Plan de datos' in txt or '11. Secuencia' in txt):
        capture = False
    
    if capture and txt:
        print(f"[{p.style.name}]: {txt}")
