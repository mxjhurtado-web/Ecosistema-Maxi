import docx

doc = docx.Document('backend/templates/master_work_instructions_template.docx')

print("=== TABLE 1 (LEGAL FRAMEWORK) ===")
t1 = doc.tables[1]
for r_idx, row in enumerate(t1.rows):
    print(f"\nRow {r_idx}:")
    for c_idx, c in enumerate(row.cells):
        print(f"  Col {c_idx}:")
        for p_idx, p in enumerate(c.paragraphs):
            runs_info = [(r.text, r.font.name, r.font.size, r.font.bold) for r in p.runs]
            print(f"    P{p_idx}: text='{p.text}' runs={runs_info}")

print("\n=== TABLE 3 (VALIDITY & STAKEHOLDERS) ===")
t3 = doc.tables[3]
for r_idx, row in enumerate(t3.rows):
    print(f"\nRow {r_idx}:")
    for c_idx, c in enumerate(row.cells):
        print(f"  Col {c_idx}:")
        for p_idx, p in enumerate(c.paragraphs):
            runs_info = [(r.text, r.font.name, r.font.size, r.font.bold) for r in p.runs]
            print(f"    P{p_idx}: text='{p.text}' runs={runs_info}")
