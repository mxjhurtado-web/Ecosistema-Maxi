import sqlite3

conn = sqlite3.connect('temis.db')
cursor = conn.cursor()

cursor.execute('SELECT id, name, created_at FROM projects ORDER BY created_at DESC')
projects = cursor.fetchall()

print(f'Total projects: {len(projects)}')
for p in projects:
    print(f'  - {p[1]} (ID: {p[0][:8]}...)')

conn.close()
