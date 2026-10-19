import openpyxl
import sys

sys.stdout.reconfigure(encoding='utf-8')

fp = r'C:\Users\User\Downloads\Backlog_Scrum_area_tecnica_TEMIS.xlsx'
wb = openpyxl.load_workbook(fp)

for sname in wb.sheetnames:
    ws = wb[sname]
    print(f"\nSheet: {sname}")
    # inspect row 2 cell 1 font, fill, border
    c = ws.cell(2, 1)
    print(f"  Sample Cell (2,1): val={c.value}")
    if c.font:
        print(f"    Font: name={c.font.name}, size={c.font.size}, bold={c.font.bold}, color={c.font.color.rgb if c.font.color else None}")
    if c.fill:
        print(f"    Fill: fill_type={c.fill.fill_type}, start_color={c.fill.start_color.rgb if c.fill.start_color else None}")
