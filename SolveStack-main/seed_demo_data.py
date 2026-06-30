"""
Seed a reliable demo dataset for recruiter demos or hosted preview environments.

This intentionally avoids live scrapers, external API credentials, and embedding
generation so the demo path remains dependable.
"""
from datetime import date, datetime, timedelta

from database import SessionLocal, engine
from auth import get_password_hash
from models import Base, CollaborationGroup, Problem, SquadMessage, User


DEMO_USER = {
    "email": "demo@solvestack.dev",
    "username": "demo_builder",
    "password": "Demo@12345",
    "skills": ["React", "FastAPI", "PostgreSQL", "Search"],
    "interests": ["portfolio projects", "developer tools", "collaboration"],
}


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
        "difficulty_level": 3,
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
        "difficulty_level": 2,
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
        "difficulty_level": 1,
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
        "difficulty_level": 3,
        "technical_depth_score": 0.81,
        "industry_impact_score": 0.7,
        "cognitive_complexity_score": 0.79,
        "signal_quality_score": 0.68,
        "upvotes": 24,
        "comment_count": 8,
    },
]


ADDITIONAL_DEMO_BLUEPRINTS = [
    {
        "title": "Multi-tenant feature flag audit trail for B2B SaaS",
        "description": "Product teams need to know who changed a rollout, which customers were affected, and how to roll back safely when a flag causes a production issue.",
        "source": "github/demo",
        "suggested_tech": "FastAPI, PostgreSQL, React, Audit Logs",
        "tags": ["feature-flags", "audit-logs", "saas", "postgresql"],
    },
    {
        "title": "Clinic no-show prediction and waitlist optimizer",
        "description": "Small clinics lose capacity when patients miss appointments. Build a dashboard that predicts risky slots, suggests reminders, and fills openings from a waitlist.",
        "source": "hackernews/demo",
        "suggested_tech": "Python, FastAPI, PostgreSQL, React",
        "tags": ["healthcare", "prediction", "scheduling", "dashboard"],
    },
    {
        "title": "Personal finance anomaly detector for subscription creep",
        "description": "Users often miss duplicate charges, silent subscription increases, and unusual merchant patterns. Detect anomalies and explain them in plain language.",
        "source": "reddit/demo",
        "suggested_tech": "Plaid API, Python, PostgreSQL, React",
        "tags": ["fintech", "anomaly-detection", "subscriptions", "alerts"],
    },
    {
        "title": "Teacher workload planner with rubric-aware grading queues",
        "description": "Teachers need to balance grading, feedback quality, and deadline pressure. Prioritize submissions by risk, rubric complexity, and student support needs.",
        "source": "stackoverflow/demo",
        "suggested_tech": "React, FastAPI, PostgreSQL, Queueing",
        "tags": ["edtech", "workflow", "prioritization", "rubrics"],
    },
    {
        "title": "Pull request risk scorer for small engineering teams",
        "description": "Reviewers need a fast way to spot risky PRs. Score changes using touched modules, churn, tests, ownership, and historical incident links.",
        "source": "github/demo",
        "suggested_tech": "GitHub API, Python, GraphQL, React",
        "tags": ["developer-tools", "code-review", "risk-scoring", "github"],
    },
    {
        "title": "Customer support duplicate ticket clusterer",
        "description": "Support teams waste time triaging repeated reports of the same bug. Cluster incoming tickets, surface likely root causes, and link related incidents.",
        "source": "hackernews/demo",
        "suggested_tech": "Embeddings, FastAPI, PostgreSQL, React",
        "tags": ["support", "clustering", "embeddings", "incident-management"],
    },
    {
        "title": "Warehouse cold-chain breach monitor",
        "description": "Food and pharma teams need to track temperature excursions, affected batches, compliance notes, and escalation timelines from sensor feeds.",
        "source": "reddit/demo",
        "suggested_tech": "IoT, FastAPI, Timeseries, React",
        "tags": ["logistics", "iot", "compliance", "monitoring"],
    },
    {
        "title": "Open-source maintainer burnout signal dashboard",
        "description": "Popular repositories accumulate issues faster than maintainers can respond. Detect burnout signals from response times, stale labels, and contributor load.",
        "source": "github/demo",
        "suggested_tech": "GitHub API, PostgreSQL, React, Analytics",
        "tags": ["open-source", "analytics", "maintainer-tools", "github"],
    },
    {
        "title": "Secure document expiry tracker for HR teams",
        "description": "HR teams need reminders for contracts, visas, certifications, and policy acknowledgements with role-based access and audit history.",
        "source": "stackoverflow/demo",
        "suggested_tech": "FastAPI, PostgreSQL, RBAC, React",
        "tags": ["hrtech", "rbac", "documents", "compliance"],
    },
    {
        "title": "AI prompt regression test suite for product teams",
        "description": "Teams changing prompts need to know whether outputs got worse. Store test cases, compare model responses, and flag quality regressions before release.",
        "source": "hackernews/demo",
        "suggested_tech": "Python, FastAPI, LLM Eval, React",
        "tags": ["ai", "evaluation", "testing", "prompt-engineering"],
    },
    {
        "title": "Municipal issue routing system for citizen reports",
        "description": "City staff receive duplicate pothole, lighting, and sanitation reports. Route issues by location, category, urgency, and department capacity.",
        "source": "reddit/demo",
        "suggested_tech": "GIS, FastAPI, PostgreSQL, React",
        "tags": ["civic-tech", "gis", "routing", "operations"],
    },
    {
        "title": "Release notes generator from commits and tickets",
        "description": "Teams struggle to turn commits and Jira tickets into useful customer-facing release notes. Generate grouped, editable notes with risk labels.",
        "source": "github/demo",
        "suggested_tech": "GitHub API, NLP, FastAPI, React",
        "tags": ["release-management", "nlp", "developer-tools", "jira"],
    },
    {
        "title": "Restaurant prep demand forecaster",
        "description": "Small restaurants need to estimate prep quantities from reservations, weather, events, and historical sales to reduce waste and stockouts.",
        "source": "hackernews/demo",
        "suggested_tech": "Python, Forecasting, PostgreSQL, Dashboard",
        "tags": ["foodtech", "forecasting", "inventory", "dashboard"],
    },
    {
        "title": "Security checklist evidence collector for startups",
        "description": "Startups preparing for vendor reviews need to gather policies, screenshots, access reviews, and evidence into a repeatable security packet.",
        "source": "stackoverflow/demo",
        "suggested_tech": "FastAPI, S3, PostgreSQL, React",
        "tags": ["security", "compliance", "evidence", "startups"],
    },
    {
        "title": "Student project scope validator",
        "description": "Students often choose projects that are too broad or too shallow. Score scope, suggest MVP boundaries, and produce milestone plans.",
        "source": "reddit/demo",
        "suggested_tech": "React, FastAPI, Rules Engine, PostgreSQL",
        "tags": ["education", "planning", "portfolio", "project-scoping"],
    },
    {
        "title": "Cloud cost spike explainer for side projects",
        "description": "Developers get surprised by cloud bills. Ingest usage exports, detect spikes, map them to deploys, and explain the likely cause.",
        "source": "github/demo",
        "suggested_tech": "AWS Cost Explorer, Python, React, PostgreSQL",
        "tags": ["cloud-cost", "observability", "aws", "finops"],
    },
    {
        "title": "Internal tool access review assistant",
        "description": "Managers need quarterly access reviews that are not spreadsheet chaos. Show who has access, why, last activity, and suggested removals.",
        "source": "hackernews/demo",
        "suggested_tech": "FastAPI, PostgreSQL, RBAC, React",
        "tags": ["security", "access-review", "rbac", "workflow"],
    },
    {
        "title": "Remote team decision log with context recovery",
        "description": "Remote teams forget why decisions were made. Capture decisions, alternatives, owners, source links, and revisit dates in a searchable timeline.",
        "source": "reddit/demo",
        "suggested_tech": "PostgreSQL, Search, React, FastAPI",
        "tags": ["knowledge-management", "remote-work", "search", "timeline"],
    },
    {
        "title": "API contract drift detector for microservices",
        "description": "Frontend and backend teams break each other when APIs drift. Compare OpenAPI snapshots, identify breaking changes, and notify owners.",
        "source": "stackoverflow/demo",
        "suggested_tech": "OpenAPI, FastAPI, PostgreSQL, CI",
        "tags": ["api", "microservices", "contract-testing", "ci"],
    },
    {
        "title": "Community moderation queue prioritizer",
        "description": "Moderators need to triage reports by harm, repeat offenders, confidence, and freshness while keeping an audit trail of actions.",
        "source": "reddit/demo",
        "suggested_tech": "React, FastAPI, PostgreSQL, Moderation",
        "tags": ["trust-safety", "moderation", "prioritization", "audit"],
    },
    {
        "title": "Medication refill coordination tracker",
        "description": "Patients, pharmacies, and clinics lose time coordinating refills. Track refill status, blockers, messages, and escalation deadlines.",
        "source": "hackernews/demo",
        "suggested_tech": "FastAPI, PostgreSQL, React, Notifications",
        "tags": ["healthcare", "workflow", "notifications", "status-tracking"],
    },
    {
        "title": "Test flakiness investigator for CI pipelines",
        "description": "Teams ignore flaky tests until confidence collapses. Track flaky runs, environment patterns, recent code owners, and quarantine decisions.",
        "source": "github/demo",
        "suggested_tech": "CI API, Python, PostgreSQL, React",
        "tags": ["ci", "testing", "developer-tools", "analytics"],
    },
    {
        "title": "Vendor risk questionnaire auto-fill workspace",
        "description": "Security and sales teams repeatedly answer similar questionnaires. Reuse approved answers, flag stale evidence, and track review status.",
        "source": "stackoverflow/demo",
        "suggested_tech": "FastAPI, PostgreSQL, Search, React",
        "tags": ["vendor-risk", "security", "workflow", "search"],
    },
    {
        "title": "Local service outage map for small ISPs",
        "description": "Small ISPs need to combine customer reports, router telemetry, and field technician updates into a real-time outage map.",
        "source": "reddit/demo",
        "suggested_tech": "Maps, WebSockets, FastAPI, PostgreSQL",
        "tags": ["networking", "maps", "realtime", "operations"],
    },
    {
        "title": "Knowledge base freshness monitor",
        "description": "Support docs silently rot as products change. Detect stale articles from ticket deflections, product changes, and unanswered searches.",
        "source": "hackernews/demo",
        "suggested_tech": "Search Analytics, FastAPI, PostgreSQL, React",
        "tags": ["documentation", "analytics", "support", "knowledge-base"],
    },
    {
        "title": "Interview prep tracker tied to target job descriptions",
        "description": "Candidates need to map practice sessions to actual role requirements. Track gaps, spaced repetition, and evidence-ready project stories.",
        "source": "reddit/demo",
        "suggested_tech": "React, FastAPI, PostgreSQL, NLP",
        "tags": ["career-tools", "learning", "nlp", "planning"],
    },
    {
        "title": "Privacy request workflow for small apps",
        "description": "Small teams need a GDPR-style workflow for export/delete requests, identity checks, deadlines, and audit logs without buying enterprise tools.",
        "source": "stackoverflow/demo",
        "suggested_tech": "FastAPI, PostgreSQL, Background Jobs, React",
        "tags": ["privacy", "gdpr", "workflow", "audit-logs"],
    },
    {
        "title": "Fleet maintenance early warning board",
        "description": "Operations teams need to predict vehicle issues using service history, driver reports, mileage, and parts availability.",
        "source": "hackernews/demo",
        "suggested_tech": "Python, PostgreSQL, React, Forecasting",
        "tags": ["fleet", "maintenance", "forecasting", "operations"],
    },
    {
        "title": "Meeting action item accountability tracker",
        "description": "Action items disappear after meetings. Extract tasks, assign owners, track blockers, and link outcomes back to decisions.",
        "source": "reddit/demo",
        "suggested_tech": "NLP, FastAPI, PostgreSQL, React",
        "tags": ["productivity", "nlp", "task-tracking", "teams"],
    },
    {
        "title": "Dependency upgrade blast-radius planner",
        "description": "Teams delay dependency upgrades because impact is unclear. Map packages to services, tests, owners, vulnerabilities, and rollout steps.",
        "source": "github/demo",
        "suggested_tech": "Dependency Graph, Python, PostgreSQL, React",
        "tags": ["dependencies", "security", "developer-tools", "planning"],
    },
]


for offset, item in enumerate(ADDITIONAL_DEMO_BLUEPRINTS, start=1):
    source_key = item["source"].split("/")[0]
    slug = (
        item["title"].lower()
        .replace("-", " ")
        .replace("/", " ")
        .replace(" ", "_")
    )
    score = 72 + ((offset * 7) % 22)
    difficulty_level = [1, 2, 3, 2, 1, 3][(offset - 1) % 6]
    DEMO_PROBLEMS.append({
        **item,
        "source_id": f"demo_{slug[:54]}",
        "reference_link": f"https://demo.solvestack.local/problems/{slug.replace('_', '-')[:72]}",
        "engineering_impact_score": score,
        "difficulty_level": difficulty_level,
        "technical_depth_score": round(0.58 + ((offset * 5) % 33) / 100, 2),
        "industry_impact_score": round(0.6 + ((offset * 7) % 31) / 100, 2),
        "cognitive_complexity_score": round(0.55 + ((offset * 11) % 35) / 100, 2),
        "signal_quality_score": round(0.62 + ((offset * 13) % 29) / 100, 2),
        "upvotes": 18 + ((offset * 9) % 55),
        "comment_count": 4 + ((offset * 5) % 22),
    })


def seed_demo_data() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    inserted = 0

    try:
        demo_user = db.query(User).filter(User.email == DEMO_USER["email"]).first()
        if not demo_user:
            demo_user = User(
                email=DEMO_USER["email"],
                username=DEMO_USER["username"],
                hashed_password=get_password_hash(DEMO_USER["password"]),
                skills=DEMO_USER["skills"],
                interests=DEMO_USER["interests"],
                activity_score=68,
            )
            db.add(demo_user)
            db.flush()
        else:
            demo_user.username = DEMO_USER["username"]
            demo_user.hashed_password = get_password_hash(DEMO_USER["password"])
            demo_user.skills = DEMO_USER["skills"]
            demo_user.interests = DEMO_USER["interests"]
            demo_user.activity_score = max(demo_user.activity_score or 0, 68)

        seeded_problems = []
        for index, item in enumerate(DEMO_PROBLEMS):
            exists = db.query(Problem).filter(Problem.reference_link == item["reference_link"]).first()
            if exists:
                exists.difficulty_level = item.get("difficulty_level", exists.difficulty_level or 2)
                exists.difficulty_score = item["engineering_impact_score"] / 100
                exists.technical_depth_score = item["technical_depth_score"]
                exists.industry_impact_score = item["industry_impact_score"]
                exists.cognitive_complexity_score = item["cognitive_complexity_score"]
                exists.signal_quality_score = item["signal_quality_score"]
                exists.engineering_impact_score = item["engineering_impact_score"]
                exists.upvotes = item["upvotes"]
                exists.comment_count = item["comment_count"]
                exists.engagement_score = float(item["upvotes"] + item["comment_count"])
                seeded_problems.append(exists)
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
                difficulty_level=item.get("difficulty_level", 2),
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
            seeded_problems.append(problem)
            inserted += 1

        db.flush()

        for problem in seeded_problems[:3]:
            if demo_user not in problem.interested_users:
                problem.interested_users.append(demo_user)

        if seeded_problems:
            squad_templates = [
                (
                    0,
                    "Incident Memory Builders",
                    "Designing the schema, search flow, and incident timeline UX for engineering teams.",
                    "Welcome to the recruiter demo. This seeded squad shows the collaboration flow without depending on live scraper data.",
                ),
                (
                    1,
                    "Latency Watch",
                    "Building FastAPI middleware, slow-query tracking, and release-to-release regression charts.",
                    "First milestone: capture p95 latency by endpoint and link spikes to deploy timestamps.",
                ),
                (
                    4,
                    "PR Risk Lab",
                    "Exploring GitHub signals, ownership metadata, and test coverage to flag risky pull requests.",
                    "The interesting part is not the score alone; it is explaining why a review deserves attention.",
                ),
                (
                    9,
                    "Prompt QA Bench",
                    "Creating repeatable prompt regression tests for product teams shipping AI features.",
                    "We are collecting golden examples and comparing output quality across prompt versions.",
                ),
            ]

            for problem_index, name, description, message in squad_templates:
                if problem_index >= len(seeded_problems):
                    continue

                squad = db.query(CollaborationGroup).filter(
                    CollaborationGroup.problem_id == seeded_problems[problem_index].ps_id,
                    CollaborationGroup.leader_id == demo_user.id,
                    CollaborationGroup.name == name,
                ).first()
                if not squad:
                    squad = CollaborationGroup(
                        problem_id=seeded_problems[problem_index].ps_id,
                        name=name,
                        description=description,
                        leader_id=demo_user.id,
                        is_active=True,
                    )
                    squad.members.append(demo_user)
                    db.add(squad)
                    db.flush()
                elif demo_user not in squad.members:
                    squad.members.append(demo_user)

                existing_message = db.query(SquadMessage).filter(
                    SquadMessage.squad_id == squad.id,
                    SquadMessage.sender_id == demo_user.id,
                    SquadMessage.content == message,
                ).first()
                if not existing_message:
                    db.add(SquadMessage(
                        squad_id=squad.id,
                        sender_id=demo_user.id,
                        content=message,
                    ))

        db.commit()
        total = db.query(Problem).count()
        print(
            f"Seeded {inserted} demo problems. Total problems: {total}. "
            f"Demo login: {DEMO_USER['email']} / {DEMO_USER['password']}"
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_data()
