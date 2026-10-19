import openpyxl
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
wb = openpyxl.load_workbook(fp, data_only=True)

ws_backlog = wb['Backlog Scrum Técnico TEMIS']
print("=== BACKLOG ITEMS ===")
headers = [ws_backlog.cell(1, c).value for c in range(1, ws_backlog.max_column + 1)]
print(f"Headers: {headers}\n")

for r in range(2, ws_backlog.max_row + 1):
    vals = [ws_backlog.cell(r, c).value for c in range(1, ws_backlog.max_column + 1)]
    print(f"Item {r-1}: ID={vals[0]} | Module={vals[1]} | Type={vals[2]} | Status={vals[12] if len(vals)>12 else 'N/A'} | Title={str(vals[3])[:60]}")

ws_agenda = wb['📅 Agenda Ejecutiva']
print("\n=== AGENDA EJECUTIVA ===")
for r in range(4, ws_agenda.max_row + 1):
    vals = [ws_agenda.cell(r, c).value for c in range(1, ws_agenda.max_column + 1)]
    print(f"Row {r}: {vals}")
