import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

load_dotenv()


def get_engine():
    """
    Creates and returns a SQLAlchemy engine for connecting to a PostgreSQL database.
    The connection parameters are retrieved from environment variables:
    - POSTGRES_USER: The username for the database (default: 'postgres').
    - POSTGRES_PASSWORD: The password for the database (default: 'mysecretpassword').
    - POSTGRES_HOST: The hostname of the database server (default: 'localhost').
    - POSTGRES_PORT: The port number of the database server (default: '5432').
    - POSTGRES_DB: The name of the database (default: 'postgres').
    Returns:
        sqlalchemy.engine.base.Engine: A SQLAlchemy engine instance configured for the PostgreSQL database.
    """
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "mysecretpassword")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "postgres")

    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{db}"

    return create_engine(connection_string)


def get_session(engine):
    """
    Creates and returns a SQLAlchemy session factory bound to the provided engine.
    Args:
        engine (sqlalchemy.engine.base.Engine): The SQLAlchemy engine to bind the session to.
    Returns:
        sqlalchemy.orm.session.Session: A new SQLAlchemy session instance.
    """
    Session = sessionmaker(bind=engine)
    return Session()
