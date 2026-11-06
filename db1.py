import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# Load enviroment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not found in .env file")

# Create PostgreSQL connection
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

def get_data(query, params=None):
    """Execute SQL query and return a Pandas DataFrame."""
    with engine.connect() as connection:
        return pd.read_sql(
            text(query), 
            connection, 
            params=params or {}
        )

def test_connection():
    """Test PostgreSQL database connection."""
    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), version()")
        )
        return result.fetchone()