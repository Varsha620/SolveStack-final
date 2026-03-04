from database import SessionLocal
from engineering_scoring_engine import get_scoring_engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backfill_eis():
    db = SessionLocal()
    try:
        engine = get_scoring_engine()
        print("Starting EIS backfill...")
        count = engine.process_all_problems(db)
        print(f"Successfully backfilled EIS for {count} problems.")
    except Exception as e:
        print(f"Error during backfill: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    backfill_eis()
