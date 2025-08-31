from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import pandas as pd
from db.schema import Base, Fund, Issuer, Filing, HoldinsRaw as HoldingRaw
import os
from dotenv import load_dotenv
load_dotenv()

## Connect to DB and Create tables
Base = declarative_base()

# postgresql://username:password@host:port/database_name
DATABASE_URL = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

Base.metadata.create_all(engine) # create tables