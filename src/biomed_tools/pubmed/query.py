"""Functions to query the PubMed database."""

import pandas as pd
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, sessionmaker

from .models import (
    Publication,
    SearchTerm,
    SearchToPublication,
    create_tables,
    get_engine,
)
from .utils import normalize_query


def get_db_session() -> Session:
    """Creates and returns a new SQLAlchemy session."""
    engine = get_engine()
    create_tables()  # Ensure tables are created before a session is made
    Session = sessionmaker(bind=engine)
    return Session()


def summarize_database(session: Session) -> None:
    """Prints a high-level summary of the database content."""
    pub_count = session.query(func.count(Publication.pmid)).scalar()
    search_count = session.query(func.count(SearchTerm.id)).scalar()
    full_text_count = (
        session.query(Publication).filter(Publication.full_text.isnot(None)).count()
    )
    min_date, max_date = session.query(
        func.min(Publication.pub_date), func.max(Publication.pub_date)
    ).one()

    print("--- Database Summary ---")
    print(f"Total Publications: {pub_count}")
    print(f"Total Search Terms: {search_count}")
    if pub_count > 0:
        print(
            f"Publications with Full Text: {full_text_count} ({full_text_count/pub_count:.1%} of total)"
        )
    else:
        print("Publications with Full Text: 0")
    print(f"Publication Date Range: {min_date} to {max_date}")
    print("------------------------")


def get_all_publications(session: Session, columns: list = None) -> pd.DataFrame:
    """
    Retrieves all publications from the database.
    """
    if columns is None:
        columns = ["pmid", "pmcid", "title", "journal", "pub_date"]

    query = session.query(*(getattr(Publication, c) for c in columns))
    df = pd.read_sql_query(query.statement, session.bind)
    return df


def get_publication_by_pmid(session: Session, pmid: str) -> pd.DataFrame:
    """
    Finds a single publication by its PMID.
    """
    query = session.query(Publication).filter(Publication.pmid == pmid)
    df = pd.read_sql_query(query.statement, session.bind)
    return df


def find_publications_by_keyword(
    session: Session, keyword: str, search_in: list = None
) -> pd.DataFrame:
    """
    Searches for publications containing a keyword in the title or abstract.
    """
    if search_in is None:
        search_in = ["title", "abstract"]

    filters = []
    if "title" in search_in:
        filters.append(Publication.title.ilike(f"%{keyword}%"))
    if "abstract" in search_in:
        filters.append(Publication.abstract.ilike(f"%{keyword}%"))
    if "full_text" in search_in:
        filters.append(Publication.full_text.ilike(f"%{keyword}%"))

    if not filters:
        raise ValueError("The 'search_in' list cannot be empty.")

    query = session.query(Publication).filter(or_(*filters))
    df = pd.read_sql_query(query.statement, session.bind)
    return df


def get_publications_for_search(
    session: Session, search_query: str
) -> pd.DataFrame:
    """
    Retrieves all publications associated with a specific, previously run search query.
    """
    normalized = normalize_query(search_query)
    query = (
        session.query(Publication)
        .join(SearchToPublication)
        .join(SearchTerm)
        .filter(SearchTerm.term == normalized)
    )
    df = pd.read_sql_query(query.statement, session.bind)
    return df
