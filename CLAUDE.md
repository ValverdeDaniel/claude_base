# Project Overview

Full-stack web application starter with Django + React.

## Architecture

- **Backend**: Django 4.2 + Django REST Framework
- **Frontend**: React 19 with Vite + React Router 7
- **Database**: PostgreSQL 15
- **Containerization**: Docker + docker-compose
- **Deployment target**: Railway (Docker-based)

## Development Commands

```bash
# Start all services
docker compose up --build

# Run in background
docker compose up --build -d

# Stop services
docker compose down

# Run migrations
docker compose exec backend python manage.py migrate

# Create superuser
docker compose exec backend python manage.py createsuperuser

# View logs
docker compose logs -f backend
docker compose logs -f frontend
```

## API Routes

All auth endpoints are under `/api/auth/`:

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/auth/login/` | No | Login with username/password |
| POST | `/api/auth/signup/` | No | Register new account |
| POST | `/api/auth/logout/` | Yes | Delete auth token |
| GET/PATCH | `/api/auth/profile/` | Yes | Get or update profile |
| POST | `/api/auth/change-password/` | Yes | Change password |
| POST | `/api/auth/request-password-reset/` | No | Request reset email |
| POST | `/api/auth/reset-password/` | No | Reset password with token |

## Notes

- Do not modify `docker-compose.yml`, `Dockerfile`, or `start.sh` unless explicitly asked
- Frontend dev server runs on port 4000, backend on port 8000
- PostgreSQL data persists in a Docker volume (`postgres_data`)
