import os
import psycopg2
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load database credentials
load_dotenv()

def get_connection():
    """Create postgreSQL database connection."""

    connection = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "electronics_dw"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD")

    )

    return connection

def test_connection():
    """Test PostgreSQL connection."""

    try:
        conn = get_connection()

        cursor = conn.cursor()
        cursor.execute("SELECT version();")

        result = cursor.fetchone()

        cursor.close()
        conn.close()

        print("Database connection successful!")
        print(result[0])

        return True
    
    except Exception as e:
        print(f"Database connection failed: {e}")
        return False


def get_data(query):
    """Execute SQL query and return DataFrame."""

    conn = None

    try:
        conn =get_connection()

        df = pd.read_sql_query(query, conn)

        return df

    except Exception as e:
        print(f"Query execution failed: {e}")
        raise

    finally:
        if conn is not None:
            conn.close()