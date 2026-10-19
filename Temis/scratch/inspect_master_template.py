import docx

file_path = r'C:\Users\User\Downloads\Plantilla_Maestra_Oficial_Work_Instructions_TEMIS.docx'
doc = docx.Document(file_path)

print(f"=== DOCUMENT SUMMARY ===")
print(f"Sections: {len(doc.sections)}")
print(f"Paragraphs: {len(doc.paragraphs)}")
print(f"Tables: {len(doc.tables)}")

print("\n=== PARAGRAPHS ===")
for i, p in enumerate(doc.paragraphs):
    if p.text.strip():
        runs_info = [f"'{r.text}'(b={r.font.bold},sz={r.font.size},fn={r.font.name})" for r in p.runs]
        print(f"P[{i}] style={p.style.name} align={p.alignment}: {p.text}")
        print(f"     Runs: {runs_info}")

for i, t in enumerate(doc.tables):
    print(f"\n=================== TABLE {i+1} ({len(t.rows)} rows x {len(t.columns)} cols) ===================")
    for r_i, r in enumerate(t.rows):
        print(f"\n--- Table {i+1} Row {r_i} ---")
        for c_i, c in enumerate(r.cells):
            tcPr = c._tc.tcPr
            shd = tcPr.find(docx.oxml.ns.qn('w:shd')) if tcPr is not None else None
            fill = shd.get(docx.oxml.ns.qn('w:fill')) if shd is not None else 'None'
            paras = [p.text.strip() for p in c.paragraphs if p.text.strip()]
            print(f"  Col {c_i} (w={c.width}, fill={fill}): {paras}")
