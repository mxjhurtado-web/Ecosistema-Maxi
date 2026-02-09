import sys
import os

filepath = r"c:\Users\User\Ecosistema-Maxi\Middleware\respondio-middleware\api\config_manager.py"
with open(filepath, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    # Add mcp_token to default and fallback MCPConfig initializations
    if 'retry_delay=settings.MCP_RETRY_DELAY,' in line and 'mcp_token=' not in line:
        new_lines.append(line)
        indent = line[:line.find('retry_delay')]
        new_lines.append(f"{indent}mcp_token=settings.MCP_TOKEN,\n")
    else:
        new_lines.append(line)

with open(filepath, 'w') as f:
    f.writelines(new_lines)
print("Updated successfully")
