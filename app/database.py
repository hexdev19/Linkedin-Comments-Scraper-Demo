from sqlalchemy import create_engine, Column, String, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

engine = create_engine("sqlite:///data/linkedin.db", echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, unique=True, index=True)
    email = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class Comment(Base):
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True)
    session_id = Column(String, index=True)
    author = Column(String, index=True)
    timestamp = Column(String)
    original_text = Column(Text)
    cleaned_text = Column(Text, index=True)
    text_length = Column(Integer)
    scraped_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
