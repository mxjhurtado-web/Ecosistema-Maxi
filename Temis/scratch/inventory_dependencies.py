import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

keywords = ['governance', 'work_plan', 'daily_log', 'active_view', 'project_charter', 'charter', 'audit_modal', 'sponsor']

matches = {}
search_dirs = [
    r'C:\Users\User\Ecosistema-Maxi\Temis\temis_web',
    r'C:\Users\User\Ecosistema-Maxi\Temis\backend'
]

for sdir in search_dirs:
    for root, dirs, files in os.walk(sdir):
        if any(p in root for p in ['__pycache__', '.pytest_cache']):
            continue
        for f in files:
            if f.endswith('.py'):
                fp = os.path.join(root, f)
                rel_p = os.path.relpath(fp, r'C:\Users\User\Ecosistema-Maxi\Temis')
                try:
                    with open(fp, 'r', encoding='utf-8', errors='ignore') as fh:
                        lines = fh.readlines()
                        for i, l in enumerate(lines):
                            for kw in keywords:
                                if kw in l.lower():
                                    if rel_p not in matches:
                                        matches[rel_p] = []
                                    matches[rel_p].append((i + 1, kw, l.strip()[:100]))
                                    break
                except Exception as e:
                    pass

print(f"Total files with references: {len(matches)}")
for f, items in sorted(matches.items()):
    print(f"\nFile: {f} ({len(items)} references)")
    for line_num, kw, txt in items[:6]:
        print(f"  Line {line_num} [{kw}]: {txt}")
    if len(items) > 6:
        print(f"  ... (+ {len(items)-6} more references)")
