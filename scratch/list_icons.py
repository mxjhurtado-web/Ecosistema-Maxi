import os
import re

pattern = re.compile(r'rx\.icon\([\'"]([^\'"]+)[\'"]')
icons = set()
for root, dirs, files in os.walk('Temis/temis_web'):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as fp:
                for match in pattern.finditer(fp.read()):
                    icons.add((match.group(1), path))

for icon, path in sorted(list(icons)):
    print(f"{icon:30} -> {path}")
