# SolveStack - Real-World Problem Discovery Platform

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-green)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-blue)](https://www.postgresql.org/)

SolveStack is a full-stack platform for discovering and curating real-world technical problems from developer communities. It combines scraping, backend APIs, search, scoring, authentication, and team collaboration flows so builders can find meaningful project ideas instead of generic clone apps.

## Current Status

This repository is a production-minded portfolio project, not a fully hosted production service yet.

Implemented and working locally:
- FastAPI backend with JWT authentication.
- SQLAlchemy models for users, problems, interests, squads, join requests, and squad messages.
- SQLite development mode and PostgreSQL-ready configuration.
- Alembic migrations for database schema management.
- Multi-source scraping modules for Reddit, Stack Overflow, Hacker News, and GitHub.
- Problem listing, details, trending, interests, semantic search, impact explanations, and prototype-plan endpoints.
- Squad collaboration: create squads, request to join, accept/reject members, leave/delete squads, and WebSocket chat.
- React/Vite frontend in `../solvestack-frontend`.
- Environment-based frontend/backend configuration for deployment.

In progress or intentionally optional:
- Backend deployment to Render/Railway/Fly.io and hosted PostgreSQL.
- Production monitoring and logging.
- CI pipeline.
- Payment/subscription features. Stripe fields exist in the data model, but payment flows are not implemented.
- Firebase. Earlier docs mention Firebase, but current chat uses FastAPI WebSockets and database-persisted squad messages.

## Core Features

- Multi-source discovery: scrape technical problems from Reddit, Stack Overflow, Hacker News, and GitHub.
- Problem cleaning and scoring: normalize text, reduce duplicates, classify difficulty, and compute engineering-impact signals.
- Search: keyword, hybrid, and semantic-style search endpoints.
- Authentication: register/login with JWT-based protected routes.
- Personal workflow: mark problems as interesting and view saved items.
- Collaboration: form squads around problems, manage join requests, and chat in real time over WebSockets.
- Deployment hardening: environment-based CORS, required production JWT secret, frontend API/WS URL configuration.

## Tech Stack

- Backend: Python, FastAPI, SQLAlchemy, Pydantic, JWT auth.
- Database: SQLite for local development, PostgreSQL-ready production configuration, Alembic migrations.
- Search/AI: sentence-transformer/embedding support, engineering-impact scoring, reranking and explanation services.
- Frontend: React, Vite, TypeScript, Tailwind CSS, lucide-react.
- Tooling: pytest-style scripts, Postman-friendly API, Docker-ready dependency structure.

## Live Demo

Frontend demo: `https://varsha620.github.io/SolveStack-final/`

The live demo uses frontend fallback data when a hosted backend is not connected, so reviewers can still explore the product flow.

## Quick Start

### Backend

```bash
cd SolveStack-main
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Backend URLs:
- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`

### Frontend

```bash
cd solvestack-frontend
npm install
copy .env.example .env
npm run dev
```

Frontend defaults to:
- API: `http://localhost:8000`
- WebSocket: derived from `VITE_API_URL`

## Environment Variables

Backend `.env`:

```bash
ENVIRONMENT=development
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=120
DATABASE_URL=sqlite:///./solvestack_dev.db
FRONTEND_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

Production backend must set:

```bash
ENVIRONMENT=production
SECRET_KEY=<strong unique secret>
FRONTEND_ORIGINS=https://your-frontend-domain.example
DATABASE_URL=postgresql://user:password@host:5432/solvestack
```

Optional scraper credentials:

```bash
REDDIT_CLIENT_ID=
REDDIT_CLIENT_SECRET=
REDDIT_USER_AGENT=
STACKEXCHANGE_KEY=
GITHUB_TOKEN=
```

Frontend `.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=
```

For production:

```bash
VITE_API_URL=https://your-backend-domain.example
VITE_WS_URL=
```

If `VITE_WS_URL` is empty, the frontend derives it from `VITE_API_URL` by converting `http` to `ws` and `https` to `wss`.

## API Overview

Authentication:
- `POST /register`
- `POST /login`
- `GET /me`

Problems:
- `GET /problems`
- `GET /problems/{problem_id}`
- `GET /problems/trending`
- `POST /scrape/all`

Search and intelligence:
- `GET /search`
- `GET /search/hybrid`
- `GET /search/semantic`
- `GET /shelf`
- `GET /shelf/{problem_id}/explain`
- `GET /problems/{problem_id}/prototype`
- `GET /analytics/shelf`

Interests and collaboration:
- `POST /interest`
- `DELETE /interest/{problem_id}`
- `GET /me/interests`
- `GET /me/squads`
- `POST /collaborate/request`
- `POST /collaborate/accept`
- `POST /collaborate/reject`
- `GET /collaborate/{problem_id}`

Squads:
- `GET /squads`
- `POST /squads`
- `GET /squads/{squad_id}`
- `POST /squads/{squad_id}/join`
- `POST /squads/{squad_id}/accept/{user_id}`
- `POST /squads/{squad_id}/reject/{user_id}`
- `GET /squads/{squad_id}/messages`
- `DELETE /squads/{squad_id}`
- `POST /squads/{squad_id}/leave`
- `WS /ws/squad/{squad_id}`

Debug/health:
- `GET /`
- `GET /db-info`

## Testing And Verification

Useful local checks:

```bash
python -m py_compile main.py auth.py models.py schemas.py database.py
python verify_db.py
python test_backend.py
python test_individual_scrapers.py
python test_scrape_all_endpoint.py
```

Seed reliable demo data without live scraper credentials:

```bash
python seed_demo_data.py
```

Frontend:

```bash
npm install
npm run build
```

## Honest Limitations

- Live scraping depends on external APIs, credentials, quotas, and network availability.
- Some older phase docs mention Firebase, Stripe, voting, and claims. The current recruiter-facing scope is the API and frontend flows listed above.
- The app still needs hosted backend deployment, monitoring, and CI before it should be described as full-stack production deployed.
- CPU-based AI/embedding workflows can be slow depending on model and dataset size.

## Portfolio Positioning

SolveStack is best presented as a full-stack engineering project focused on:
- FastAPI REST API design.
- PostgreSQL-ready data modeling.
- Authenticated user workflows.
- Search and AI-assisted ranking.
- Real-time collaboration with WebSockets.
- Practical deployment hardening and honest production tradeoffs.
