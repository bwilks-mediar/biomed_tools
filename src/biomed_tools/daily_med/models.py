"""Database models for DailyMed Miner."""

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
    create_engine,
    func,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from .config import DB_URL, ensure_dir_exists

Base = declarative_base()

class SearchTerm(Base):
    """Represents a normalized search query."""
    __tablename__ = "search_terms"
    id = Column(Integer, primary_key=True)
    term = Column(Text, unique=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    # You might link searches to results if needed, but for now simple tracking

    def __repr__(self) -> str:
        return f"<SearchTerm(id={self.id}, term='{self.term}')>"

class Drug(Base):
    """Represents a drug product from DailyMed."""
    __tablename__ = "drugs"
    
    set_id = Column(String, primary_key=True)
    drug_name = Column(String, nullable=True)
    spl_version = Column(Integer, nullable=True)
    published_date = Column(String, nullable=True)
    
    # Store raw JSON if structure is complex and variable?
    # For now, stick to basic fields.
    
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    ndcs = relationship("NDC", back_populates="drug")

    def __repr__(self) -> str:
        return f"<Drug(set_id='{self.set_id}', name='{self.drug_name}')>"

class NDC(Base):
    """Represents a National Drug Code."""
    __tablename__ = "ndcs"
    
    ndc = Column(String, primary_key=True)
    set_id = Column(String, ForeignKey("drugs.set_id"))
    
    drug = relationship("Drug", back_populates="ndcs")

    def __repr__(self) -> str:
        return f"<NDC(ndc='{self.ndc}')>"

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
