import openpyxl

wb = openpyxl.load_workbook(r'C:\Users\User\Downloads\Plantilla Matriz Sipoc.xlsx')
ws = wb.active

print("=== EXCEL COLUMN WIDTHS ===")
for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K']:
    dim = ws.column_dimensions.get(col)
    w = dim.width if dim else None
    print(f"Col {col}: width={w}")

print("\n=== ROWS STYLING ===")
for r in range(1, 22):
    c2 = ws.cell(r, 2)
    c3 = ws.cell(r, 3)
    c4 = ws.cell(r, 4)
    c5 = ws.cell(r, 5)
    c6 = ws.cell(r, 6)
    
    fill_c2 = c2.fill.start_color.rgb if c2.fill and c2.fill.start_color else None
    fill_c6 = c6.fill.start_color.rgb if c6.fill and c6.fill.start_color else None
    
    font_c2 = f"{c2.font.name} {c2.font.size}pt bold={c2.font.bold}" if c2.font else ""
    
    print(f"Row {r:2d} (height={ws.row_dimensions[r].height}): fill={fill_c2}, font={font_c2}")
    print(f"       C2={repr(c2.value)} | C3={repr(c3.value)} | C4={repr(c4.value)} | C5={repr(c5.value)} | C6={repr(c6.value)}")
