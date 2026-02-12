import sqlalchemy
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import Problem
from scoring_engine import compute_problem_quality_score, calculate_problem_difficulty

def recalculate_all():
    db: Session = SessionLocal()
    try:
        problems = db.query(Problem).all()
        print(f"🔄 Recalculating scores for {len(problems)} problems...")
        
        count = 0
        for problem in problems:
            # Re-run scoring
            result = compute_problem_quality_score(problem)
            difficulty = result['difficulty']
            quality = result['quality_score']
            
            
            print(f"[PS-{problem.ps_id}] '{problem.title[:30]}...' -> Quality: {quality}, Diff: {difficulty}")
            
            count += 1
            
        print(f"✅ Completed calculation for {count} problems.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    recalculate_all()
