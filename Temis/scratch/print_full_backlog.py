import openpyxl
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
wb = openpyxl.load_workbook(fp, data_only=True)

for name in wb.sheetnames:
    ws = wb[name]
    print(f"\n========================================================")
    print(f"SHEET: '{name}' | Total Rows: {ws.max_row} | Total Cols: {ws.max_column}")
    print(f"========================================================")
    for r in range(1, ws.max_row + 1):
        vals = [ws.cell(r, c).value for c in range(1, ws.max_column + 1)]
        if any(v is not None for v in vals):
            clean = [str(v).replace('\n', ' ') if v is not None else '' for v in vals]
            print(f"R{r:02d}: {clean}")
