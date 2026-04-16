# Claude Base

A ready-to-use starter application for building full-stack web apps with Django and React.

## What Is This?

This is a base application I built to handle the repetitive setup that every web project needs. It comes with user authentication (login, signup, password reset) already working out of the box, so you can skip the boilerplate and start building your actual idea right away.

If you're looking to build a web application and want a solid starting point, feel free to use this. If it saves you time on the initial setup and gives you a reliable foundation to build on, then it's doing its job.

## Why Django?

Django is a well-established Python web framework that comes with a lot of functionality built in — user authentication, database management, an admin interface, security protections, and more. Rather than piecing together dozens of separate libraries, Django gives you a proven, all-in-one toolkit that has been used in production by companies of all sizes for years.

## Why Docker?

Docker packages everything your application needs (Python, Node.js, PostgreSQL) into containers. This means:

- **Consistent setup** — it works the same on every machine, no "it works on my computer" issues
- **No manual installs** — you don't need to install Python, Node, or PostgreSQL yourself
- **Database included** — PostgreSQL runs inside a container with a fixed version, so everyone is on the same database
- **One command to start** — `docker compose up --build` launches the entire application

## What's Included

- **Backend** — Django 4.2 with Django REST Framework for building APIs
- **Frontend** — React 19 with Vite (a fast development server) and React Router for page navigation
- **Database** — PostgreSQL 15, running inside Docker
- **Authentication** — Login, signup, logout, profile management, and password reset — all wired up and ready to use

## Getting Started

### Prerequisites

You only need one thing installed on your machine:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) — download and install it for your operating system

### Running the Application

1. Clone this repository to your machine
2. Open a terminal in the project folder
3. Run the following command:

```bash
docker compose up --build
```

4. Wait for everything to start up (the first time may take a few minutes as it downloads dependencies)
5. Open your browser:
   - **Frontend** — [http://localhost:4000](http://localhost:4000)
   - **Backend API** — [http://localhost:8000](http://localhost:8000)

### Useful Commands

```bash
# Start the application
docker compose up --build

# Start in the background (frees up your terminal)
docker compose up --build -d

# Stop the application
docker compose down

# Run database migrations
docker compose exec backend python manage.py migrate

# Create an admin account
docker compose exec backend python manage.py createsuperuser

# View backend logs
docker compose logs -f backend

# View frontend logs
docker compose logs -f frontend
```

## Project Structure

```
claude_base/
├── backend/          # Django project settings and configuration
├── users/            # User authentication app (login, signup, etc.)
├── admin_panel/      # Admin tools and utilities
├── frontend/         # React application
├── docker-compose.yml
├── Dockerfile
├── requirements.txt  # Python dependencies
└── manage.py         # Django management script
```

## Building On Top of This

This project is meant to be a starting point. Here are some ideas for what to do next:

1. **Add your own Django apps** — run `docker compose exec backend python manage.py startapp your_app_name` to create a new module for your features
2. **Add frontend pages** — create new React components in the `frontend/src/components/` folder and add routes in the app
3. **Extend the user model** — the authentication system is ready to be customized if you need additional user fields

## Tech Stack

| Layer      | Technology                     |
|------------|--------------------------------|
| Backend    | Django 4.2, Django REST Framework |
| Frontend   | React 19, Vite, React Router 7   |
| Database   | PostgreSQL 15                     |
| Containers | Docker, Docker Compose            |
