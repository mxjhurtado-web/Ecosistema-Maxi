
import sys
import os
import importlib.util

print(f"Python Executable: {sys.executable}")
print(f"CWD: {os.getcwd()}")

required_modules = [
    "mutagen",
    "soundfile",
    "numpy",
    "pandas",
    "google.generativeai",
    "dotenv",
    "tkinter"
]

print("\n--- Checking Modules ---")
all_ok = True
for mod in required_modules:
    try:
        if "." in mod:
            importlib.import_module(mod)
        else:
            __import__(mod)
        print(f"✅ {mod} found")
    except ImportError as e:
        print(f"❌ {mod} MISSING: {e}")
        all_ok = False

print("\n--- Checking App Imports ---")
try:
    from athenas_lite.config import settings
    print(f"✅ Config loaded. GEMINI_KEY present in code? {'Yes' if settings.GEMINI_API_KEY else 'No (Empty but config loads)'}")
    
    from athenas_lite.services import system_tools
    print("✅ System Tools loaded")
    
    if hasattr(system_tools, 'convert_to_wav'):
        print("✅ convert_to_wav available")
    else:
        print("❌ convert_to_wav MISSING in system_tools")
        all_ok = False

except Exception as e:
    print(f"❌ App Import Error: {e}")
    all_ok = False

if all_ok:
    print("\n🎉 VERIFICATION SUCCESSFUL: Ready to launch!")
else:
    print("\n⚠️ VERIFICATION FAILED: Fix missing modules.")
