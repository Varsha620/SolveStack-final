"""
Seed a reliable demo dataset for recruiter demos or hosted preview environments.

This intentionally avoids live scrapers, external API credentials, and embedding
generation so the demo path remains dependable.
"""
from datetime import date, datetime, timedelta

from database import SessionLocal, engine
from models import Base, Problem


DEMO_PROBLEMS = [
    {
        "title": "Local-first incident knowledge base for small engineering teams",
        "description": "Teams lose debugging history across Slack threads, tickets, and postmortems. Build a searchable incident memory that links symptoms, fixes, owners, and follow-up tasks.",
        "source": "github/demo",
        "source_id": "demo_incident_memory",
        "suggested_tech": "FastAPI, PostgreSQL, React, Search",
        "reference_link": "https://demo.solvestack.local/problems/incident-memory",
        "tags": ["fastapi", "postgresql", "search", "incident-management"],
        "engineering_impact_score": 86,
        "technical_depth_score": 0.84,
        "industry_impact_score": 0.82,
        "cognitive_complexity_score": 0.76,
        "signal_quality_score": 0.9,
        "upvotes": 42,
        "comment_count": 13,
    },
    {
        "title": "API latency regression monitor for FastAPI deployments",
        "description": "A lightweight observability dashboard that tracks endpoint latency, error rate, slow queries, and deploy-to-deploy regressions for small backend projects.",
        "source": "stackoverflow/demo",
        "source_id": "demo_latency_monitor",
        "suggested_tech": "FastAPI, PostgreSQL, Recharts, Docker",
        "reference_link": "https://demo.solvestack.local/problems/latency-monitor",
        "tags": ["fastapi", "observability", "postgresql", "dashboard"],
        "engineering_impact_score": 78,
        "technical_depth_score": 0.72,
        "industry_impact_score": 0.74,
        "cognitive_complexity_score": 0.66,
        "signal_quality_score": 0.8,
        "upvotes": 31,
        "comment_count": 9,
    },
    {
        "title": "Resume-aware project recommender for junior developers",
        "description": "Given a resume and target role, recommend project ideas that fill skill gaps and produce measurable portfolio bullets.",
        "source": "hackernews/demo",
        "source_id": "demo_resume_recommender",
        "suggested_tech": "React, Python, Embeddings, PostgreSQL",
        "reference_link": "https://demo.solvestack.local/problems/resume-recommender",
        "tags": ["react", "python", "embeddings", "career-tools"],
        "engineering_impact_score": 81,
        "technical_depth_score": 0.7,
        "industry_impact_score": 0.88,
        "cognitive_complexity_score": 0.69,
        "signal_quality_score": 0.86,
        "upvotes": 48,
        "comment_count": 17,
    },
    {
        "title": "Offline-first field service checklist app",
        "description": "Technicians need structured checklists that work without network access, then sync cleanly with conflict resolution when back online.",
        "source": "reddit/demo",
        "source_id": "demo_offline_checklists",
        "suggested_tech": "IndexedDB, FastAPI, PostgreSQL, Sync",
        "reference_link": "https://demo.solvestack.local/problems/offline-checklists",
        "tags": ["offline-first", "sync", "fastapi", "indexeddb"],
        "engineering_impact_score": 74,
        "technical_depth_score": 0.81,
        "industry_impact_score": 0.7,
        "cognitive_complexity_score": 0.79,
        "signal_quality_score": 0.68,
        "upvotes": 24,
        "comment_count": 8,
    },
]


def seed_demo_data() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    inserted = 0

    try:
        for index, item in enumerate(DEMO_PROBLEMS):
            exists = db.query(Problem).filter(Problem.reference_link == item["reference_link"]).first()
            if exists:
                continue

            description = item["description"]
            problem = Problem(
                title=item["title"],
                description=description,
                raw_title=item["title"],
                raw_description=description,
                cleaned_title=item["title"],
                cleaned_description=description,
                normalized_title=item["title"].lower(),
                source=item["source"],
                source_id=item["source_id"],
                date=date.today() - timedelta(days=index),
                suggested_tech=item["suggested_tech"],
                author_name="SolveStack Demo",
                author_id="demo",
                reference_link=item["reference_link"],
                tags=item["tags"],
                raw_tags=item["tags"],
                scraped_at=datetime.utcnow() - timedelta(days=index),
                cleaned_at=datetime.utcnow(),
                difficulty_score=item["engineering_impact_score"] / 100,
                difficulty_level=3 if item["engineering_impact_score"] >= 80 else 2,
                upvotes=item["upvotes"],
                comment_count=item["comment_count"],
                engagement_score=float(item["upvotes"] + item["comment_count"]),
                text_length=len(description),
                word_count=len(description.split()),
                technical_depth_score=item["technical_depth_score"],
                industry_impact_score=item["industry_impact_score"],
                cognitive_complexity_score=item["cognitive_complexity_score"],
                signal_quality_score=item["signal_quality_score"],
                engineering_impact_score=item["engineering_impact_score"],
            )
            db.add(problem)
            inserted += 1

        db.commit()
        total = db.query(Problem).count()
        print(f"Seeded {inserted} demo problems. Total problems: {total}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
