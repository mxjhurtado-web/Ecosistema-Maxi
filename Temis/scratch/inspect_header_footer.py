import docx

doc = docx.Document('backend/templates/master_work_instructions_template.docx')

print("=== ALL PARAGRAPHS IN DOC ===")
for p_idx, p in enumerate(doc.paragraphs):
    print(f"P{p_idx}: text='{p.text}' style='{p.style.name}'")

print("\n=== HEADER & FOOTER ===")
for s_idx, sec in enumerate(doc.sections):
    print(f"Section {s_idx}:")
    for hp_idx, hp in enumerate(sec.header.paragraphs):
        print(f"  Header P{hp_idx}: text='{hp.text}'")
    for ht_idx, ht in enumerate(sec.header.tables):
        print(f"  Header Table {ht_idx}: {len(ht.rows)} rows x {len(ht.columns)} cols")
        for r_i, r in enumerate(ht.rows):
            print(f"    R{r_i}: {[c.text.replace(chr(10), ' ') for c in r.cells]}")
    for fp_idx, fp in enumerate(sec.footer.paragraphs):
        print(f"  Footer P{fp_idx}: text='{fp.text}'")
