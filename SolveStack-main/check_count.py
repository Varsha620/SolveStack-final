from database import engine
from sqlalchemy import text
with engine.connect() as conn:
    print("RESULT:", conn.execute(text("SELECT count(*) FROM problems")).scalar())
