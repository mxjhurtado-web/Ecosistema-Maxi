#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Extract text from Formato Temis.pdf
"""

import PyPDF2

pdf_path = "Formato Temis.pdf"

try:
    with open(pdf_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        
        print(f"Total pages: {len(pdf_reader.pages)}\n")
        print("="*80)
        
        for page_num in range(len(pdf_reader.pages)):
            print(f"\n--- PAGE {page_num + 1} ---\n")
            page = pdf_reader.pages[page_num]
            text = page.extract_text()
            print(text)
            print("\n" + "="*80)
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
