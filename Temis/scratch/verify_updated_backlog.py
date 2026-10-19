import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
wb = openpyxl.load_workbook(fp, data_only=True)

print("=== VERIFYING AGENDA EJECUTIVA ===")
ws_agenda = wb['📅 Agenda Ejecutiva']
for r in range(4, ws_agenda.max_row + 1):
    vals = [ws_agenda.cell(r, c).value for c in range(1, ws_agenda.max_column + 1)]
    print(f"R{r:02d}: {vals}")

print("\n=== VERIFYING BACKLOG ITEMS (LAST 8) ===")
ws_backlog = wb['Backlog Scrum Técnico TEMIS']
for r in range(max(2, ws_backlog.max_row - 8), ws_backlog.max_row + 1):
    vals = [ws_backlog.cell(r, c).value for c in [1, 2, 3, 8, 9, 10, 13, 14, 17]]
    print(f"R{r:02d}: {vals}")

print("\n=== VERIFYING HISTORIAL COMMITS (FIRST 10) ===")
ws_hist = wb['Historial Commits']
for r in range(1, 12):
    vals = [ws_hist.cell(r, c).value for c in [1, 2, 4, 5, 6]]
    print(f"R{r:02d}: {vals}")
