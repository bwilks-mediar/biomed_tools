"""Database models for OpenFDA module."""

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    create_engine,
    func,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from .config import DB_URL, ensure_dir_exists

Base = declarative_base()

class SearchTerm(Base):
    """Represents a normalized search query."""
    __tablename__ = "search_terms"
    id = Column(Integer, primary_key=True)
    term = Column(Text, nullable=False)
    endpoint = Column(String, nullable=False, default="event")
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        UniqueConstraint('term', 'endpoint', name='uix_term_endpoint'),
    )
    
    events = relationship("SearchToEvent", back_populates="search")
    labels = relationship("SearchToLabel", back_populates="search")
    ndcs = relationship("SearchToNDC", back_populates="search")
    enforcements = relationship("SearchToEnforcement", back_populates="search")
    drugsfda = relationship("SearchToDrugsFDA", back_populates="search")

    def __repr__(self) -> str:
        return f"<SearchTerm(id={self.id}, term='{self.term}', endpoint='{self.endpoint}')>"

# --- Adverse Events ---
class DrugEvent(Base):
    """Represents a FAERS adverse event report."""
    __tablename__ = "drug_events"
    
    safetyreportid = Column(String, primary_key=True)
    receivedate = Column(String) # YYYYMMDD
    serious = Column(String) # "1" or "2"
    seriousnessdeath = Column(String)
    seriousnesshospitalization = Column(String)
    
    # Patient info
    patient_onsetage = Column(String)
    patient_onsetageunit = Column(String)
    patient_sex = Column(String) # 1=Male, 2=Female
    patient_weight = Column(String)
    
    data = Column(JSON) # Store full JSON
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    drugs = relationship("DrugEventDrug", back_populates="event", cascade="all, delete-orphan")
    reactions = relationship("DrugEventReaction", back_populates="event", cascade="all, delete-orphan")
    searches = relationship("SearchToEvent", back_populates="event")

    def __repr__(self) -> str:
        return f"<DrugEvent(safetyreportid='{self.safetyreportid}')>"

class DrugEventDrug(Base):
    """Drugs involved in the adverse event."""
    __tablename__ = "drug_event_drugs"
    id = Column(Integer, primary_key=True)
    safetyreportid = Column(String, ForeignKey("drug_events.safetyreportid"))
    
    medicinalproduct = Column(String)
    drugcharacterization = Column(String) # 1=Suspect, 2=Concomitant, 3=Interacting
    drugindication = Column(String)
    
    # OpenFDA annotated fields (can be lists, joining with |)
    brand_name = Column(Text)
    generic_name = Column(Text)
    substance_name = Column(Text)
    manufacturer_name = Column(Text)
    
    event = relationship("DrugEvent", back_populates="drugs")

class DrugEventReaction(Base):
    """Reactions reported in the adverse event."""
    __tablename__ = "drug_event_reactions"
    id = Column(Integer, primary_key=True)
    safetyreportid = Column(String, ForeignKey("drug_events.safetyreportid"))
    
    reactionmeddrapt = Column(String) # MedDRA Preferred Term
    reactionoutcome = Column(String)
    
    event = relationship("DrugEvent", back_populates="reactions")

class SearchToEvent(Base):
    """Association table linking search terms to drug events."""
    __tablename__ = "search_to_events"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    safetyreportid = Column(String, ForeignKey("drug_events.safetyreportid"), primary_key=True)

    search = relationship("SearchTerm", back_populates="events")
    event = relationship("DrugEvent", back_populates="searches")

# --- Product Labeling ---
class DrugLabel(Base):
    """Represents a Drug Label (SPL)."""
    __tablename__ = "drug_labels"
    id = Column(String, primary_key=True) # set_id is usually the unique key, but sometimes multiple versions exist. API uses ID field.
    set_id = Column(String, nullable=False)
    spl_id = Column(String)
    
    brand_name = Column(Text) # JSON list stored as text
    generic_name = Column(Text) # JSON list stored as text
    manufacturer_name = Column(Text) # JSON list stored as text
    effective_time = Column(String)
    
    data = Column(JSON) # Store full JSON for flexibility
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    searches = relationship("SearchToLabel", back_populates="label")

class SearchToLabel(Base):
    __tablename__ = "search_to_labels"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    label_id = Column(String, ForeignKey("drug_labels.id"), primary_key=True)
    search = relationship("SearchTerm", back_populates="labels")
    label = relationship("DrugLabel", back_populates="searches")

# --- NDC Directory ---
class DrugNDC(Base):
    """Represents a Drug NDC Directory entry."""
    __tablename__ = "drug_ndc"
    product_id = Column(String, primary_key=True)
    product_ndc = Column(String)
    
    brand_name = Column(Text)
    generic_name = Column(Text)
    labeler_name = Column(Text)
    finished = Column(Boolean)
    dea_schedule = Column(String)
    
    data = Column(JSON)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    searches = relationship("SearchToNDC", back_populates="ndc")

class SearchToNDC(Base):
    __tablename__ = "search_to_ndc"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    ndc_id = Column(String, ForeignKey("drug_ndc.product_id"), primary_key=True)
    search = relationship("SearchTerm", back_populates="ndcs")
    ndc = relationship("DrugNDC", back_populates="searches")

# --- Enforcement Reports ---
class DrugEnforcement(Base):
    """Represents a Drug Recall Enforcement Report."""
    __tablename__ = "drug_enforcement"
    recall_number = Column(String, primary_key=True)
    reason_for_recall = Column(Text)
    status = Column(String)
    distribution_pattern = Column(Text)
    product_description = Column(Text)
    recall_initiation_date = Column(String)
    
    data = Column(JSON)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    searches = relationship("SearchToEnforcement", back_populates="enforcement")

class SearchToEnforcement(Base):
    __tablename__ = "search_to_enforcement"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    recall_number = Column(String, ForeignKey("drug_enforcement.recall_number"), primary_key=True)
    search = relationship("SearchTerm", back_populates="enforcements")
    enforcement = relationship("DrugEnforcement", back_populates="searches")

# --- Drugs@FDA ---
class DrugAtFDA(Base):
    """Represents a Drugs@FDA entry."""
    __tablename__ = "drug_drugsfda"
    application_number = Column(String, primary_key=True)
    sponsor_name = Column(String)
    
    products = Column(JSON) # List of products
    
    data = Column(JSON)
    
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    searches = relationship("SearchToDrugsFDA", back_populates="drugsfda")

class SearchToDrugsFDA(Base):
    __tablename__ = "search_to_drugsfda"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    app_num = Column(String, ForeignKey("drug_drugsfda.application_number"), primary_key=True)
    search = relationship("SearchTerm", back_populates="drugsfda")
    drugsfda = relationship("DrugAtFDA", back_populates="searches")

def get_engine():
    """Creates and returns a SQLAlchemy engine, ensuring the data directory exists."""
    ensure_dir_exists()
    return create_engine(DB_URL)

def create_tables():
    """Creates all database tables defined in the models."""
    engine = get_engine()
    Base.metadata.create_all(engine)

def get_session():
    """Creates and returns a new SQLAlchemy session."""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()
