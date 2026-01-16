#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
EOD Scheduler for TEMIS
Automatically processes End of Day at 8 PM
"""

import schedule
import threading
import time
from datetime import datetime


class EODScheduler:
    """Scheduler for automatic EOD processing"""
    
    def __init__(self, eod_callback):
        """
        Initialize scheduler
        Args:
            eod_callback: Function to call at 8 PM
        """
        self.eod_callback = eod_callback
        self.running = False
        self.thread = None
    
    def start(self):
        """Start the scheduler"""
        if self.running:
            return
        
        # Schedule EOD at 8 PM daily
        schedule.every().day.at("20:00").do(self._trigger_eod)
        
        self.running = True
        
        # Run scheduler in background thread
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        
        print("[EOD Scheduler] Started - EOD will run daily at 8:00 PM")
    
    def stop(self):
        """Stop the scheduler"""
        self.running = False
        schedule.clear()
        print("[EOD Scheduler] Stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop"""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def _trigger_eod(self):
        """Trigger EOD processing"""
        print(f"[EOD Scheduler] Triggering EOD at {datetime.now().strftime('%H:%M')}")
        try:
            self.eod_callback()
        except Exception as e:
            print(f"[EOD Scheduler] Error during EOD: {e}")
