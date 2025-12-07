from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from journey_service.app.db import SessionLocal
from journey_service.app.api import process_missing_checkouts

scheduler = BackgroundScheduler()

def job_wrapper():
    """
    Wraps the process_missing_checkouts logic with a manual DB session.
    """
    print(f"[{datetime.now()}] Starting Scheduled Job: Process Missing Checkouts")
    db = SessionLocal()
    try:
        # process_missing_checkouts returns a dict, we can print it
        result = process_missing_checkouts(db)
        print(f"[{datetime.now()}] Job Completed: {result}")
    except Exception as e:
        print(f"[{datetime.now()}] Job Failed: {e}")
    finally:
        db.close()

def start_scheduler():
    # Run every 1 hour (interval)
    scheduler.add_job(job_wrapper, 'interval', hours=1, id='process_missing_checkouts')
    scheduler.start()
    print("APScheduler started: process_missing_checkouts every 1 hour.")
