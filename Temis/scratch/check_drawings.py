import docx

doc = docx.Document('backend/templates/master_work_instructions_template.docx')
for t_idx, tbl in enumerate(doc.tables):
    for r_idx, row in enumerate(tbl.rows):
        for c_idx, c in enumerate(row.cells):
            xml_txt = c._element.xml
            if 'w:drawing' in xml_txt or 'w:pict' in xml_txt or 'r:embed' in xml_txt:
                print(f"Table {t_idx} Row {r_idx} Col {c_idx} has drawing/image! Cell text: '{c.text.strip()}'")
