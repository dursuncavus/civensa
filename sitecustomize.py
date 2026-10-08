import os

url = os.environ.get("DATABASE_URL", "")
if url.startswith("postgresql://"):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://" + url[len("postgresql://"):]
elif url.startswith("postgres://"):
    os.environ["DATABASE_URL"] = "postgresql+psycopg://" + url[len("postgres://"):]
