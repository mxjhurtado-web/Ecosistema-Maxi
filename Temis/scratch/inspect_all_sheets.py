import openpyxl
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
wb = openpyxl.load_workbook(fp, data_only=True)

print("=== WORKBOOK SHEETS ===")
for i, name in enumerate(wb.sheetnames):
    ws = wb[name]
    print(f"\nSheet {i+1}: '{name}' ({ws.max_row} rows x {ws.max_column} cols)")
    # Print headers (row 1 to 5)
    for r in range(1, min(ws.max_row + 1, 8)):
        vals = [ws.cell(r, c).value for c in range(1, min(ws.max_column + 1, 12))]
        if any(v is not None for v in vals):
            clean = [str(v).replace('\n', ' ') if v is not None else '' for v in vals]
            print(f"  R{r:02d}: {clean}")
