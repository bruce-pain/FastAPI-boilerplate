# FastAPI Boilerplate

A simple FastAPI backend boilerplate with authentication, database integration, and common utilities.

## Tech Stack

- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Alembic** - Database migrations
- **uv** - Python package manager
- **JWT** - Authentication
- **Passlib** - Password hashing
- **SlowAPI** - Rate limiting
- **Ruff** - Linting and formatting

## Project Structure

```
├── app/
│   ├── core/
│   │   ├── base/            # Base classes (model, schema, repository)
│   │   ├── dependencies/    # Dependency injection
│   │   ├── middleware/      # Custom middleware
│   │   ├── config.py        # Application settings
│   │   ├── database.py      # Database connection
│   │   ├── logger.py        # Logging configuration
│   │   └── response_messages.py
│   ├── features/
│   │   ├── auth/            # Authentication module
│   │   │   ├── models.py
│   │   │   ├── repository.py
│   │   │   ├── routes.py
│   │   │   ├── schemas.py
│   │   │   ├── service.py
│   │   │   ├── jwt.py
│   │   │   └── password.py
│   │   └── router.py        # Feature router aggregation
│   └── main.py              # Application entry point
├── alembic/                 # Database migrations
├── tests/                   # Test suite
├── Makefile                 # Development commands
├── pyproject.toml           # Project configuration
└── .env                     # Environment variables
```

## Features

- **JWT Authentication** - Token-based auth with access and refresh tokens
- **Password Hashing** - Secure password storage with bcrypt
- **Database Migrations** - Alembic for version control
- **Rate Limiting** - Built-in rate limiting with SlowAPI
- **Structured Logging** - Application logging to file
- **Repository Pattern** - Clean data access layer
- **Base Classes** - Reusable model, schema, and repository base classes

## Setup

### Clone your repo

- Clone your repository after creating it with this template.

- Install [uv](https://github.com/astral-sh/uv):

```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

- Create a `.env` file by copying the `.env.sample` file:

```sh
cp .env.sample .env
```

- Fill in the environment variables in `.env` (see Environment Variables section below)

- Install project dependencies:

```sh
make install
```

- Run database migrations:

```sh
make upgrade
```

- Start the server:

```sh
make run
```

### Environment Variables

| Variable                  | Description                              |
| ------------------------- | ---------------------------------------- |
| `ENVIRONMENT`            | Environment (dev, prod)                 |
| `DATABASE_TYPE`          | Database type (postgresql)              |
| `DATABASE_NAME`          | Database name                            |
| `DATABASE_USER`          | Database username                       |
| `DATABASE_PASSWORD`      | Database password                       |
| `DATABASE_HOST`          | Database host                            |
| `DATABASE_PORT`          | Database port                            |
| `SECRET_KEY`             | JWT secret key                           |
| `ALGORITHM`              | JWT algorithm (HS256)                   |
| `ACCESS_TOKEN_EXPIRY`    | Access token expiry in hours            |
| `REFRESH_TOKEN_EXPIRY`   | Refresh token expiry in hours           |

### Setup database

To set up the database, follow the following steps:

- **Create your local database**

```bash
sudo -u <user> psql
```

```sql
CREATE DATABASE database_name;
```

- **Making migrations**

```bash
make migrate message="initial migration"
make upgrade
```

- **Adding tables and columns to models**
  After creating new tables or adding new models, make sure to run:

```bash
make migrate message="Migration message"
```

After creating new tables or adding new models, make sure you import the new model properly in the `alembic/env.py` file:

## API Documentation

Once the server is running, visit the interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Development Commands

This project uses a Makefile to manage common development tasks:

| Command          | Description                      |
| ---------------- | -------------------------------- |
| `make run`       | Start the development server     |
| `make install`   | Install project dependencies     |
| `make migrate`   | Generate a new migration         |
| `make upgrade`   | Apply all pending migrations     |
| `make downgrade` | Revert the last migration        |
| `make test`      | Run test suite                   |
| `make lint`      | Check code for linting errors    |
| `make format`    | Format codebase                  |
| `make clean`     | Remove cache and generated files |

Run `make help` to see all available commands.