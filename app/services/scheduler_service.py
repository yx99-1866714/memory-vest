import time
import threading
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Callable

class SchedulerService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        
    def add_daily_job(self, func: Callable, hour: int = 17, minute: int = 0):
        """
        Schedule a job to run every day at a specific time (e.g. 17:00 / 5 PM post-market).
        """
        self.scheduler.add_job(func, 'cron', hour=hour, minute=minute)
        print(f"Job scheduled daily at {hour:02d}:{minute:02d}")

    def start(self):
        self.scheduler.start()
        print("Scheduler started. Running in background.")
        
    def stop(self):
        self.scheduler.shutdown()
        print("Scheduler stopped.")
