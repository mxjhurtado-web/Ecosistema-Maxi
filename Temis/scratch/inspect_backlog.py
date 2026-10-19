import openpyxl
import os
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
if not os.path.exists(fp):
    fp = r'C:\Users\User\Ecosistema-Maxi\Temis\Backlog_Scrum_area_tecnica_TEMIS.xlsx'

print(f"Loading workbook from: {fp}")
wb = openpyxl.load_workbook(fp, data_only=True)
print(f"Sheet names ({len(wb.sheetnames)}): {wb.sheetnames}")

for name in wb.sheetnames:
    ws = wb[name]
    print(f"\n========================================================")
    print(f"SHEET: '{name}' | Rows: {ws.max_row} | Cols: {ws.max_column}")
    print(f"========================================================")
    
    # Print first 35 rows
    for r in range(1, min(ws.max_row + 1, 60)):
        row_vals = [ws.cell(r, c).value for c in range(1, min(ws.max_column + 1, 16))]
        if any(v is not None for v in row_vals):
            # clean formatting
            clean_row = [str(v).replace('\n', ' ') if v is not None else '' for v in row_vals]
            print(f"R{r:02d}: {clean_row}")
