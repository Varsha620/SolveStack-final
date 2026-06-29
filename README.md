# SolveStack

Full-stack problem discovery and collaboration platform for finding real-world technical project ideas from developer communities.

[Live frontend demo](https://varsha620.github.io/SolveStack-final/)  
[Backend README](SolveStack-main/README.md)  
[Frontend README](solvestack-frontend/README.md)

## What This Project Shows

SolveStack is a production-minded portfolio project built around:

- FastAPI REST API design.
- JWT authentication.
- SQLAlchemy data modeling.
- SQLite local development and PostgreSQL-ready deployment configuration.
- Multi-source problem scraping.
- Search, semantic-style retrieval, and engineering-impact scoring.
- React/Vite frontend with Tailwind CSS.
- Squad collaboration and WebSocket chat.
- Deployment hardening, demo fallback data, and honest documentation.

The live GitHub Pages demo uses frontend demo fallback data, so the interface stays reviewable even when live scraper credentials or backend hosting are not connected.

## Repository Structure

```text
SolveStack-final/
+-- SolveStack-main/        # FastAPI backend, models, scrapers, migrations, backend docs
+-- solvestack-frontend/    # React/Vite frontend, Tailwind UI, demo mode
+-- .github/workflows/      # GitHub Pages deployment workflow
+-- README.md               # Repository overview
```

GitHub shows this root `README.md` on the repository homepage. The backend and frontend folders also include their own setup notes.

## Current Status

Implemented:

- Backend API with authentication, problem discovery, search, interests, squads, and WebSocket chat.
- Frontend dashboard, problem detail, trending, interests, profile, squad list, and squad chat views.
- Tailwind/PostCSS build setup.
- In-app toast and confirmation modal system.
- Demo fallback data for reliable portfolio viewing.
- GitHub Pages frontend deployment.

Not yet fully deployed:

- Hosted backend service.
- Hosted PostgreSQL database.
- Production monitoring and CI checks.

## Quick Start

Backend:

```bash
cd SolveStack-main
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload
```

Frontend:

```bash
cd solvestack-frontend
npm install
copy .env.example .env
npm run dev
```

Optional backend demo seed:

```bash
cd SolveStack-main
python seed_demo_data.py
```

## Deployment

The frontend is deployed to GitHub Pages:

```text
https://varsha620.github.io/SolveStack-final/
```

The backend is prepared for deployment to a service such as Render, Railway, or Fly.io with a hosted PostgreSQL database.

## Portfolio Note

This project is intentionally documented as production-minded rather than fully production-hosted. That keeps the claims aligned with the current implementation while still showing backend architecture, deployment readiness, and product polish.
