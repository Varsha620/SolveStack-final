# SolveStack Frontend

React/Vite frontend for SolveStack, a production-minded portfolio project for discovering, ranking, and collaborating on real-world technical problems.

## Current Scope

Implemented:
- Welcome and landing views.
- Problem dashboard with search, filters, pagination, and scraper sync trigger.
- Trending and saved-interest views.
- Problem detail page with interest tracking, impact explanation, prototype-plan overlay, and squad discovery.
- Squad listing, creation, join requests, leader approvals, leave/delete flows, and WebSocket chat.
- Profile view backed by the FastAPI `/me` endpoint.
- Environment-based API and WebSocket configuration.
- Tailwind/PostCSS build pipeline.
- In-app toast and confirmation system.
- Demo fallback data when live backend/scraper results are unavailable.

Not currently implemented:
- Payment/subscription UI.
- Firebase chat. Chat uses the FastAPI WebSocket backend.
- A hosted demo URL. Deployment is the next portfolio polish step.
- More guided onboarding/demo walkthrough copy for first-time reviewers.

## Tech Stack

- React
- Vite
- TypeScript
- Tailwind CSS
- React Router
- lucide-react
- Recharts

## Environment

Copy `.env.example` to `.env`:

```bash
VITE_API_URL=http://localhost:8000
VITE_WS_URL=
VITE_DEMO_MODE=fallback
```

If `VITE_WS_URL` is empty, the app derives it from `VITE_API_URL`:
- `http://...` becomes `ws://...`
- `https://...` becomes `wss://...`

## Local Development

```bash
npm install
npm run dev
```

## Production Build

```bash
npm run build
```

## Backend Pairing

This frontend expects the FastAPI backend in `../SolveStack-main` to be running locally at `http://localhost:8000` unless `VITE_API_URL` is changed.
