#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEMIS Media Studio — Main Desktop Entrypoint
Desktop tool for Video Process Capture, Offline Whisper Diarization,
Smart Scene Screenshots and 1-Click TEMIS Web Sync.
"""

import os
import sys
import tkinter as tk

# Ensure current directory and subdirectories are in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Add bundled resources to PATH (like FFmpeg)
from config.settings import FFMPEG_PATH

if os.path.exists(FFMPEG_PATH):
    ffmpeg_dir = os.path.dirname(FFMPEG_PATH)
    os.environ["PATH"] = ffmpeg_dir + os.pathsep + os.environ.get("PATH", "")

from ui.main_window import TemisMediaStudioApp


def main():
    """Launch TEMIS Media Studio Application"""
    root = tk.Tk()
    app = TemisMediaStudioApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
