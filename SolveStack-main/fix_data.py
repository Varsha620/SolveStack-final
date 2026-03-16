import logging
import sys
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Force UTF-8 encoding for Windows console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Ensure we're in the right directory to import local modules
sys.path.append(os.getcwd())

from database import SessionLocal
from models import Problem
from cleaning_layer import DataCleaner
from engineering_scoring_engine import get_scoring_engine

def fix_all_data():
    """
    Recoveries data by applying DataCleaner and ScoringEngine to all records.
    """
    db = SessionLocal()
    cleaner = DataCleaner()
    scoring_engine = get_scoring_engine()
    
    try:
        problems = db.query(Problem).all()
        logger.info(f"Found {len(problems)} problems to fix.")
        
        fixed_count = 0
        for p in problems:
            # 1. Prepare data for cleaner (it expects a dict of raw fields)
            raw_data = {
                "raw_title": p.raw_title or p.title,
                "raw_description": p.raw_description or p.description,
                "raw_tags": p.tags if isinstance(p.tags, list) else [],
                "source": p.source,
                "date": p.date,
                "author_name": p.author_name,
                "author_id": p.author_id,
                "reference_link": p.reference_link,
                "source_id": p.source_id
            }
            
            # 2. Apply Cleaner
            cleaned = cleaner.clean_problem(raw_data)
            
            # 3. Update model with cleaned fields
            for key, value in cleaned.items():
                if hasattr(p, key):
                    setattr(p, key, value)
            
            # 4. Apply Scoring Engine
            scores = scoring_engine.calculate_scores(p)
            for attr, val in scores.items():
                if hasattr(p, attr):
                    setattr(p, attr, val)
            
            fixed_count += 1
            if fixed_count % 50 == 0:
                db.commit()
                logger.info(f"Fixed {fixed_count} problems...")
        
        db.commit()
        logger.info(f"Successfully fixed all {fixed_count} problems.")
        
    except Exception as e:
        logger.error(f"Error during data fix: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_all_data()
