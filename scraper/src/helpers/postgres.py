from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_engine(connection_string: str):
    """
    Creates and returns an SQLAlchemy engine for connecting to a PostgreSQL database.
    Args:
        connection_string (str): The connection string for the PostgreSQL database.
    Returns:
        sqlalchemy.engine.base.Engine: A new SQLAlchemy engine instance.
    """

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
