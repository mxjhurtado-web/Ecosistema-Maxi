import docx

doc = docx.Document('scratch/test_output_populated.docx')
print(f"Total tables: {len(doc.tables)}")

for t_idx, tbl in enumerate(doc.tables):
    print(f"\n=== TABLE {t_idx} ({len(tbl.rows)} rows) ===")
    for r_idx, row in enumerate(tbl.rows):
        cells_t = [c.text.replace('\n', ' // ') for c in row.cells]
        print(f"  R{r_idx}: {cells_t}")
