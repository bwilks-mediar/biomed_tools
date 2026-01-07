"""Database models for PubMed Miner."""

from sqlalchemy import (
    JSON,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from ..pubmed.config import DB_URL, get_db_path, ensure_dir_exists

Base = declarative_base()


class SearchTerm(Base):
    """Represents a normalized search query."""

    __tablename__ = "search_terms"
    id = Column(Integer, primary_key=True)
    term = Column(Text, unique=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    publications = relationship("SearchToPublication", back_populates="search")

    def __repr__(self) -> str:
        return f"<SearchTerm(id={self.id}, term='{self.term[:30]}...')>"


class Publication(Base):
    """Represents a single publication with extensive metadata and full text."""

    __tablename__ = "publications"
    pmid = Column(String, primary_key=True)
    pmcid = Column(String, unique=True, nullable=True)
    doi = Column(String, unique=True, nullable=True)
    title = Column(Text)
    abstract = Column(Text, nullable=True)
    authors = Column(JSON, nullable=True)
    affiliations = Column(JSON, nullable=True)
    journal = Column(Text, nullable=True)
    pub_date = Column(Date, nullable=True)
    publication_type = Column(JSON, nullable=True)
    language = Column(JSON, nullable=True)
    copyright_information = Column(Text, nullable=True)
    mesh_terms = Column(JSON, nullable=True)
    keywords = Column(JSON, nullable=True)
    full_text = Column(Text, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_checked = Column(DateTime(timezone=True), nullable=True)
    full_text_last_checked = Column(DateTime(timezone=True), nullable=True)
    searches = relationship("SearchToPublication", back_populates="publication")

    def __repr__(self) -> str:
        return f"<Publication(pmid='{self.pmid}', title='{self.title[:50]}...')>"


class SearchToPublication(Base):
    """Association table linking search terms to publications."""

    __tablename__ = "search_to_publications"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    pmid = Column(String, ForeignKey("publications.pmid"), primary_key=True)

    search = relationship("SearchTerm", back_populates="publications")
    publication = relationship("Publication", back_populates="searches")


def get_engine():
    """Creates and returns a SQLAlchemy engine, ensuring the data directory exists."""
    ensure_dir_exists()
    return create_engine(DB_URL)


def create_tables():
    """Creates all database tables defined in the models."""
    engine = get_engine()
    Base.metadata.create_all(engine)


def drop_tables():
    """Drops all database tables defined in the models."""
    engine = get_engine()
    Base.metadata.drop_all(engine)


def get_session():
    """Creates and returns a new SQLAlchemy session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
