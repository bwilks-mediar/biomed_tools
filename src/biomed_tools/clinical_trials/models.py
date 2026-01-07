"""Database models for Clinical Trials Miner."""

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
    trials = relationship("SearchToTrial", back_populates="search")

    def __repr__(self) -> str:
        return f"<SearchTerm(id={self.id}, term='{self.term[:30]}...')>"


class ClinicalTrial(Base):
    """Represents the core information for a single clinical trial."""

    __tablename__ = "clinical_trials"
    nct_id = Column(String, primary_key=True)
    brief_title = Column(Text)
    official_title = Column(Text, nullable=True)
    acronym = Column(String, nullable=True)
    overall_status = Column(String)
    start_date = Column(DateTime(timezone=True), nullable=True)
    primary_completion_date = Column(DateTime(timezone=True), nullable=True)
    completion_date = Column(DateTime(timezone=True), nullable=True)
    study_first_submit_date = Column(DateTime(timezone=True), nullable=True)
    last_update_post_date = Column(DateTime(timezone=True), nullable=True)
    enrollment_count = Column(Integer, nullable=True)
    study_type = Column(String)
    brief_summary = Column(Text, nullable=True)
    detailed_description = Column(Text, nullable=True)
    has_results = Column(Boolean)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    searches = relationship("SearchToTrial", back_populates="trial")
    organizations = relationship("TrialOrganization", back_populates="trial")
    conditions = relationship("TrialCondition", back_populates="trial")
    keywords = relationship("TrialKeyword", back_populates="trial")
    arms = relationship("Arm", back_populates="trial")
    outcomes = relationship("Outcome", back_populates="trial")
    locations = relationship("Location", back_populates="trial")
    references = relationship("Reference", back_populates="trial")
    eligibility = relationship("Eligibility", uselist=False, back_populates="trial")
    adverse_events = relationship("AdverseEvent", back_populates="trial")

    def __repr__(self) -> str:
        return f"<ClinicalTrial(nct_id='{self.nct_id}')>"


class Organization(Base):
    """Stores organization details (sponsors, etc.)."""

    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    class_ = Column("class", String)  # 'class' is a reserved keyword
    trials = relationship("TrialOrganization", back_populates="organization")


class TrialOrganization(Base):
    """Association table for trials and organizations."""

    __tablename__ = "trial_organizations"
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"), primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"), primary_key=True)
    role = Column(String)  # e.g., 'LEAD_SPONSOR', 'COLLABORATOR'
    trial = relationship("ClinicalTrial", back_populates="organizations")
    organization = relationship("Organization", back_populates="trials")


class Condition(Base):
    """Stores medical conditions."""

    __tablename__ = "conditions"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    trials = relationship("TrialCondition", back_populates="condition")


class TrialCondition(Base):
    """Association table for trials and conditions."""

    __tablename__ = "trial_conditions"
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"), primary_key=True)
    condition_id = Column(Integer, ForeignKey("conditions.id"), primary_key=True)
    trial = relationship("ClinicalTrial", back_populates="conditions")
    condition = relationship("Condition", back_populates="trials")


class Keyword(Base):
    """Stores keywords."""

    __tablename__ = "keywords"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    trials = relationship("TrialKeyword", back_populates="keyword")


class TrialKeyword(Base):
    """Association table for trials and keywords."""

    __tablename__ = "trial_keywords"
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"), primary_key=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"), primary_key=True)
    trial = relationship("ClinicalTrial", back_populates="keywords")
    keyword = relationship("Keyword", back_populates="trials")


class Intervention(Base):
    """Stores interventions (drugs, etc.)."""

    __tablename__ = "interventions"
    id = Column(Integer, primary_key=True)
    type = Column(String)
    name = Column(String)
    description = Column(Text, nullable=True)
    arms = relationship("ArmIntervention", back_populates="intervention")


class Arm(Base):
    """Stores trial arms."""

    __tablename__ = "arms"
    id = Column(Integer, primary_key=True)
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"))
    label = Column(String)
    type = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    trial = relationship("ClinicalTrial", back_populates="arms")
    interventions = relationship("ArmIntervention", back_populates="arm")


class ArmIntervention(Base):
    """Association table for arms and interventions."""

    __tablename__ = "arm_interventions"
    arm_id = Column(Integer, ForeignKey("arms.id"), primary_key=True)
    intervention_id = Column(Integer, ForeignKey("interventions.id"), primary_key=True)
    arm = relationship("Arm", back_populates="interventions")
    intervention = relationship("Intervention", back_populates="arms")


class Outcome(Base):
    """Stores outcome measures."""

    __tablename__ = "outcomes"
    id = Column(Integer, primary_key=True)
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"))
    type = Column(String)  # e.g., 'PRIMARY', 'SECONDARY'
    measure = Column(Text)
    description = Column(Text, nullable=True)
    time_frame = Column(Text, nullable=True)
    trial = relationship("ClinicalTrial", back_populates="outcomes")


class Location(Base):
    """Stores trial locations."""

    __tablename__ = "locations"
    id = Column(Integer, primary_key=True)
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"))
    facility = Column(String, nullable=True)
    city = Column(String, nullable=True)
    state = Column(String, nullable=True)
    zip = Column(String, nullable=True)
    country = Column(String)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    trial = relationship("ClinicalTrial", back_populates="locations")


class Reference(Base):
    """Stores references."""

    __tablename__ = "references"
    id = Column(Integer, primary_key=True)
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"))
    pmid = Column(String, nullable=True)
    type = Column(String, nullable=True)
    citation = Column(Text)
    trial = relationship("ClinicalTrial", back_populates="references")


class Eligibility(Base):
    """Stores eligibility criteria."""

    __tablename__ = "eligibility"
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"), primary_key=True)
    criteria = Column(Text)
    healthy_volunteers = Column(Boolean)
    sex = Column(String)
    minimum_age = Column(String, nullable=True)
    maximum_age = Column(String, nullable=True)
    trial = relationship("ClinicalTrial", back_populates="eligibility")


class AdverseEvent(Base):
    """Stores adverse event data."""

    __tablename__ = "adverse_events"
    id = Column(Integer, primary_key=True)
    trial_nct_id = Column(String, ForeignKey("clinical_trials.nct_id"))
    term = Column(String)
    organ_system = Column(String)
    source_vocabulary = Column(String)
    assessment_type = Column(String)
    is_serious = Column(Boolean)
    num_affected = Column(Integer)
    num_at_risk = Column(Integer)
    group_id = Column(String)
    group_title = Column(String)
    trial = relationship("ClinicalTrial", back_populates="adverse_events")


class SearchToTrial(Base):
    """Association table linking search terms to clinical trials."""

    __tablename__ = "search_to_trials"
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    nct_id = Column(String, ForeignKey("clinical_trials.nct_id"), primary_key=True)

    search = relationship("SearchTerm", back_populates="trials")
    trial = relationship("ClinicalTrial", back_populates="searches")


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
