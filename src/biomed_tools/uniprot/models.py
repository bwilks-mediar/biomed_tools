"""Database models for UniProt Miner."""

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
    func,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from . import config

Base = declarative_base()


class SearchTerm(Base):
    """Represents a normalized search query."""

    __tablename__ = "search_terms"
    id = Column(Integer, primary_key=True)
    term = Column(Text, unique=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    proteins = relationship("SearchToProtein", back_populates="search")

    def __repr__(self) -> str:
        return f"<SearchTerm(id={self.id}, term='{self.term[:30]}...')>"


class Protein(Base):
    """Represents a protein from UniProt."""

    __tablename__ = "proteins"
    accession = Column(String, primary_key=True)
    entry_name = Column(String, nullable=True)
    protein_name = Column(Text, nullable=True)
    gene_name = Column(String, nullable=True)
    organism_name = Column(String, nullable=True)
    organism_id = Column(Integer, nullable=True)
    sequence = Column(Text, nullable=True)
    length = Column(Integer, nullable=True)
    mass = Column(Integer, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    searches = relationship("SearchToProtein", back_populates="protein")

    def __repr__(self) -> str:
        return f"<Protein(accession='{self.accession}')>"


class SearchToProtein(Base):
    """Association table linking search terms to proteins."""

    __tablename__ = "search_to_proteins"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    accession = Column(String, ForeignKey("proteins.accession"), primary_key=True)

    search = relationship("SearchTerm", back_populates="proteins")
    protein = relationship("Protein", back_populates="searches")


def get_engine():
    """Creates and returns a SQLAlchemy engine, ensuring the data directory exists."""
    config.ensure_dir_exists()
    return create_engine(config.DB_URL)


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
