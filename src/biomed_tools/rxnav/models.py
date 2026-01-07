"""Database models for RxNav Miner."""

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

from .config import DB_URL, ensure_dir_exists

Base = declarative_base()

class SearchTerm(Base):
    """Represents a normalized search query."""
    __tablename__ = "search_terms"
    id = Column(Integer, primary_key=True)
    term = Column(Text, unique=True, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    drugs = relationship("SearchToDrug", back_populates="search")

    def __repr__(self) -> str:
        return f"<SearchTerm(id={self.id}, term='{self.term[:30]}...')>"

class Drug(Base):
    """Represents a Drug with its RxNorm ID."""
    __tablename__ = "drugs"
    id = Column(Integer, primary_key=True)
    rxcui = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    searches = relationship("SearchToDrug", back_populates="drug")
    classes = relationship("DrugClass", back_populates="drug")

    def __repr__(self) -> str:
        return f"<Drug(rxcui='{self.rxcui}', name='{self.name}')>"

class Class(Base):
    """Represents a Drug Class (e.g., MoA, EPC)."""
    __tablename__ = "classes"
    id = Column(Integer, primary_key=True)
    class_id = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    type = Column(String, nullable=True) # e.g. "MOA", "EPC"
    
    drugs = relationship("DrugClass", back_populates="class_")

    def __repr__(self) -> str:
        return f"<Class(class_id='{self.class_id}', name='{self.name}')>"

class DrugClass(Base):
    """Association table linking Drugs to Classes."""
    __tablename__ = "drug_classes"
    drug_id = Column(Integer, ForeignKey("drugs.id"), primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id"), primary_key=True)
    relation_type = Column(String, nullable=True) # e.g. "has_MoA", "member"

    drug = relationship("Drug", back_populates="classes")
    class_ = relationship("Class", back_populates="drugs")

class SearchToDrug(Base):
    """Association table linking search terms to drugs."""
    __tablename__ = "search_to_drugs"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    drug_id = Column(Integer, ForeignKey("drugs.id"), primary_key=True)

    search = relationship("SearchTerm", back_populates="drugs")
    drug = relationship("Drug", back_populates="searches")


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
