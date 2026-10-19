import docx
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Plan_Tecnico_Desacoplamiento_Gobernanza_TEMIS_AppSheet_v1.0.docx'
doc = docx.Document(fp)

print("=== HEADINGS AND KEY SECTIONS ===")
for p in doc.paragraphs:
    if p.style.name.startswith('Heading') or p.text.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.', '11.', '12.')):
        print(f"[{p.style.name}]: {p.text}")
