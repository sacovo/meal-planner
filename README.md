# Meal Planner

A modern web application for planning meals, managing recipes, and organizing shopping lists. Designed for large groups (e.g., camp planning).

## Getting Started

### Prerequisites

- [uv](https://github.com/astral-sh/uv) (Python package manager)
- [Node.js & npm](https://nodejs.org/)
- [Docker & Docker Compose](https://www.docker.com/)

### 1. Infrastructure (Database & Redis)

Start the required services using Docker Compose:

```bash
docker compose up -d
```

This starts PostgreSQL (on port 5433) and Redis (on port 6379).

### 2. Backend Setup (Django)

Install Python dependencies and set up the database:

```bash
# Install dependencies
uv sync

# Run migrations
uv run manage.py migrate

# Create a superuser (optional)
uv run manage.py createsuperuser

# Start the development server
uv run manage.py runserver
```

### 3. Frontend Setup (Vue)

Navigate to the `frontend` directory and install dependencies:

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`.

### 4. Background Tasks (Celery)

To process background tasks (like sending emails or generating reports), start the Celery worker:

```bash
uv run celery -A core worker -l info
```

## Features

- **Meal & Camp Planning:** Organize meals for specific days and adjust portions for group sizes.
- **Recipe Management:** Create, import, and scale recipes.
- **Shopping Lists:** Automatically generate shopping lists based on planned meals.
- **Inventory Tracking:** Keep track of available ingredients.
- **Invitations:** Invite collaborators to your meal plans.

## Tech Stack

- **Backend:** Django, Django Ninja (REST API), Celery, Redis, PostgreSQL.
- **Frontend:** Vue 3, Vite, Tailwind CSS (or as configured), TypeScript.
- **Development:** `uv` for Python environment management, Docker for services.
