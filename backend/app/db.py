import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Local: archivo SQLite. Produccion (Turso): definir DATABASE_URL con el
# formato "sqlite+libsql://<host>?secure=true" y TURSO_AUTH_TOKEN.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./simulador.db").strip().strip('"\'')

# Acepta tambien la URL tal como la entrega Turso (libsql://... o https://...).
for prefijo in ("libsql://", "https://"):
    if DATABASE_URL.startswith(prefijo):
        DATABASE_URL = "sqlite+libsql://" + DATABASE_URL[len(prefijo):]
if DATABASE_URL.startswith("sqlite+libsql://") and "secure=" not in DATABASE_URL:
    DATABASE_URL += ("&" if "?" in DATABASE_URL else "?") + "secure=true"

connect_args = {}
if DATABASE_URL.startswith("sqlite+libsql"):
    connect_args = {"auth_token": os.getenv("TURSO_AUTH_TOKEN", "")}
elif DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
