#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract and analyze Formato Temis.pdf structure
"""

import pdfplumber

pdf_path = "Formato Temis.pdf"

try:
    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total de páginas: {len(pdf.pages)}\n")
        print("="*80)
        
        for i, page in enumerate(pdf.pages):
            print(f"\n{'='*80}")
            print(f"PÁGINA {i + 1}")
            print('='*80)
            
            text = page.extract_text()
            if text:
                print(text)
            else:
                print("[Página sin texto extraíble]")
            
            # Extract tables if any
            tables = page.extract_tables()
            if tables:
                print(f"\n[Encontradas {len(tables)} tabla(s) en esta página]")
        
        print(f"\n{'='*80}")
        print(f"FIN DEL DOCUMENTO - {len(pdf.pages)} páginas procesadas")
        print('='*80)
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
