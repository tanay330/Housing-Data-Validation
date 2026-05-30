from sqlalchemy import create_engine # Creates connection or bridge between fastapi and postgres.
from sqlalchemy.ext.declarative import declarative_base # Base class for defining database tables.
from sqlalchemy.orm import sessionmaker # Creates a session is like a temporary conversation with the database — open, do things, close
from dotenv import load_dotenv #Reads .env file 
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()