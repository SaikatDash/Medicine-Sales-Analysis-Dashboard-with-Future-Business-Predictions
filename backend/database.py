import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use DATABASE_URL env var if provided, otherwise fallback to local SQLite file
DATABASE_URL = os.getenv('postgresql://postgres:sys449420@localhost:5432/EmployeeDatabase', 'sqlite:///./test.db')


# SQLite needs connect_args; other DBs do not
connect_args = {}
if DATABASE_URL.startswith('sqlite'):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

__all__ = ["engine", "SessionLocal", "DATABASE_URL"]


