#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract Formato Temis.pdf to file
"""

import pdfplumber
import sys

# Force UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

pdf_path = "Formato Temis.pdf"
output_file = "formato_temis_extracted.txt"

try:
    with pdfplumber.open(pdf_path) as pdf:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"Total de páginas: {len(pdf.pages)}\n\n")
            
            for i, page in enumerate(pdf.pages):
                f.write(f"\n{'='*80}\n")
                f.write(f"PÁGINA {i + 1}\n")
                f.write('='*80 + '\n\n')
                
                text = page.extract_text()
                if text:
                    f.write(text)
                    f.write('\n')
                else:
                    f.write("[Página sin texto extraíble]\n")
            
            f.write(f"\n{'='*80}\n")
            f.write(f"FIN - {len(pdf.pages)} páginas\n")
    
    print(f"✅ Contenido extraído a: {output_file}")
    print(f"📄 Total páginas: {len(pdf.pages)}")
            
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
