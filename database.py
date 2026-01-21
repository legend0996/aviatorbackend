from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# DATABASE CONFIGURATION
DB_USER = "root"
DB_PASSWORD = ""          # XAMPP default (empty)
DB_HOST = "localhost"
DB_NAME = "aviator_db"

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine)
