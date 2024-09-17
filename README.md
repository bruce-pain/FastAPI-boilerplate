# FastAPI Boilerplate

## Setup

### Clone your repo

- clone your repository after creating it with this template

### Start up the fastapi server

- Create a virtual environment.

```sh
python3 -m venv .venv
```

- Activate virtual environment.

```sh
source /path/to/venv/bin/activate`
```

- Install project dependencies `pip install -r requirements.txt`

- Create a .env file by copying the .env.sample file

`cp .env.sample .env`

- Start server.

```sh
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

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
alembic revision --autogenerate -m 'initial migration'
alembic upgrade head
```

- **Adding tables and columns to models**
  After creating new tables, or adding new models. Make sure to run

```bash
alembic revision --autogenerate -m "Migration messge"
```

After creating new tables, or adding new models. Make sure you import the new model properly in th 'api/v1/models/**init**.py file

After importing it in the init file, you don't need to import it in the /alembic/env.py file anymore
