# Copy rubricas from parent directory
import shutil
import os

source = "../../rubricas"
dest = "./rubricas"

if os.path.exists(source):
    if os.path.exists(dest):
        shutil.rmtree(dest)
    shutil.copytree(source, dest)
    print(f"✅ Copied {source} to {dest}")
    print(f"   Found {len(os.listdir(dest))} rubric files")
else:
    print(f"❌ Source directory {source} not found")
    print(f"   Please ensure rubricas folder exists in parent directory")
