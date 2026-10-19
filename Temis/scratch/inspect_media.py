import zipfile

with zipfile.ZipFile('backend/templates/master_work_instructions_template.docx', 'r') as z:
    for name in z.namelist():
        info = z.getinfo(name)
        if 'media' in name or 'image' in name or info.file_size > 10000:
            print(f"{name}: {info.file_size} bytes (compressed {info.compress_size})")
