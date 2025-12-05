
import os
import sys
import tkinter.font as tkfont

def pick_font(root):
    families = set(tkfont.families(root))
    for fam in ["Segoe UI Variable", "Segoe UI", "Calibri", "Inter", "Arial"]:
        if fam in families:
            base = fam
            break
    else:
        base = "TkDefaultFont"
    return {
        "title": tkfont.Font(root, family=base, size=22, weight="bold"),
        "body":  tkfont.Font(root, family=base, size=10),
    }

def _resource_path(filename):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.abspath("."), filename)
