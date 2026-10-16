import os

for variable in ("DATABASE_URL", "MIGRATION_DATABASE_URL"):
    url = os.environ.get(variable, "")
    if url.startswith("postgresql://"):
        os.environ[variable] = "postgresql+psycopg://" + url[len("postgresql://"):]
    elif url.startswith("postgres://"):
        os.environ[variable] = "postgresql+psycopg://" + url[len("postgres://"):]
