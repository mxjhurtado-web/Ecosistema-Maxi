#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
TEMIS Desktop Application - Main Entry Point
"""

import sys
import os

# Force UTF-8 encoding on Windows
if sys.platform == 'win32':
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding='utf-8')

import tkinter as tk
from tkinter import messagebox

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from desktop.ui.login import LoginWindow
from desktop.core.auth import AuthManager
from desktop.core.eod_scheduler import EODScheduler


def main():
    """Main entry point"""
    try:
        # Create root window (hidden initially)
        root = tk.Tk()
        root.withdraw()  # Hide main window

        # Initialize auth manager
        auth_manager = AuthManager()

        # Show login window
        login_window = LoginWindow(root, auth_manager)
        
        # Initialize EOD scheduler (will start after login)
        eod_scheduler = EODScheduler(lambda: trigger_eod(auth_manager))
        
        # Set up close handler
        root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, eod_scheduler, auth_manager))

        # Start main loop
        root.mainloop()

    except Exception as e:
        messagebox.showerror("Error Fatal", f"Error al iniciar TEMIS:\n\n{str(e)}")
        sys.exit(1)


def trigger_eod(auth_manager):
    """Trigger EOD processing for all active projects"""
    print("[EOD] Processing end of day...")
    # TODO: Implement EOD processing
    # This will call the backend endpoint to process all projects


def on_closing(root, scheduler, auth_manager):
    """Handle application closing"""
    # Stop scheduler
    scheduler.stop()
    
    # TODO: Check if there are unprocessed messages today
    # If yes, ask user if they want to process EOD before closing
    
    # Close application
    root.destroy()


if __name__ == "__main__":
    main()
