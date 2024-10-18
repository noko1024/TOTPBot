import sqlalchemy
from sqlalchemy import Column, Integer, create_engine, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = 'sqlite:///TOTPlog.db'
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class TOTPlog(Base):
    __tablename__ = 'TOTPUsed'
    id = Column(Integer, primary_key=True,autoincrement=True)
    user_id = Column(Integer)
    generated_totp = Column(String)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=sqlalchemy.func.now()
    )
Base.metadata.create_all(engine)
Session = sessionmaker(autoflush=True, bind=engine)
session = Session()