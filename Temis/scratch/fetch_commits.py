import subprocess
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

cmd = ['git', 'log', '--pretty=format:%h|||%ai|||%an|||%s', '-n', '50']
res = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')

commits = []
for line in res.stdout.strip().split('\n'):
    if '|||' in line:
        parts = line.split('|||')
        commits.append({
            'hash': parts[0],
            'date': parts[1],
            'author': parts[2],
            'message': parts[3]
        })

print(f"Total commits fetched: {len(commits)}")
with open('scratch/recent_commits.json', 'w', encoding='utf-8') as f:
    json.dump(commits, f, indent=2, ensure_ascii=False)
print("Saved to scratch/recent_commits.json")
