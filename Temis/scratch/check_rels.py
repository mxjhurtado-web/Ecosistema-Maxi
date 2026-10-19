import zipfile

with zipfile.ZipFile('backend/templates/master_work_instructions_template.docx', 'r') as z:
    for name in z.namelist():
        if name.endswith('.xml') or name.endswith('.rels'):
            content = z.read(name).decode('utf-8', errors='ignore')
            for i in range(1, 25):
                img_ref = f"image{i}."
                if img_ref in content:
                    print(f"File {name} references image{i}")
