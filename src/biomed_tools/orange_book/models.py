"""Database models for Orange Book Miner."""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    Text,
    ForeignKey,
    create_engine,
    ForeignKeyConstraint,
    func,
    DateTime
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from .config import DB_URL, ensure_dir_exists

Base = declarative_base()

class Product(Base):
    """Represents a product in the Orange Book."""
    __tablename__ = "products"

    appl_no = Column(String, primary_key=True)
    appl_type = Column(String, primary_key=True)
    product_no = Column(String, primary_key=True)
    
    ingredient = Column(String, nullable=True)
    df_route = Column(String, nullable=True)
    trade_name = Column(String, nullable=True)
    applicant = Column(String, nullable=True)
    strength = Column(String, nullable=True)
    te_code = Column(String, nullable=True)
    approval_date = Column(String, nullable=True) # Keeping as string for now to match raw data format
    rld = Column(String, nullable=True)
    rs = Column(String, nullable=True)
    type = Column(String, nullable=True)
    applicant_full_name = Column(String, nullable=True)
    
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    patents = relationship("Patent", back_populates="product", cascade="all, delete-orphan")
    exclusivity = relationship("Exclusivity", back_populates="product", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Product(appl_no='{self.appl_no}', product_no='{self.product_no}')>"

class Patent(Base):
    """Represents patent information for a product."""
    __tablename__ = "patents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    appl_no = Column(String)
    appl_type = Column(String)
    product_no = Column(String)
    
    patent_no = Column(String)
    patent_expire_date_text = Column(String, nullable=True)
    drug_substance_flag = Column(String, nullable=True)
    drug_product_flag = Column(String, nullable=True)
    patent_use_code = Column(String, nullable=True)
    delist_flag = Column(String, nullable=True)
    submission_date = Column(String, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ['appl_no', 'appl_type', 'product_no'],
            ['products.appl_no', 'products.appl_type', 'products.product_no'],
        ),
    )

    product = relationship("Product", back_populates="patents")

class Exclusivity(Base):
    """Represents exclusivity information for a product."""
    __tablename__ = "exclusivity"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    appl_no = Column(String)
    appl_type = Column(String)
    product_no = Column(String)
    
    exclusivity_code = Column(String, nullable=True)
    exclusivity_date = Column(String, nullable=True)

    __table_args__ = (
        ForeignKeyConstraint(
            ['appl_no', 'appl_type', 'product_no'],
            ['products.appl_no', 'products.appl_type', 'products.product_no'],
        ),
    )

    product = relationship("Product", back_populates="exclusivity")

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
