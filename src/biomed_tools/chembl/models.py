from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Float,
    Boolean,
    ForeignKey,
    DateTime,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session
from . import config

Base = declarative_base()

class Molecule(Base):
    __tablename__ = "molecules"

    chembl_id = Column(String, primary_key=True)
    pref_name = Column(String)
    molecule_type = Column(String)
    max_phase = Column(Integer)
    therapeutic_flag = Column(Boolean)
    structure_type = Column(String)
    inchi_key = Column(String)
    canonical_smiles = Column(Text)
    standard_inchi = Column(Text)
    
    # Additional fields
    first_approval = Column(Integer)
    black_box_warning = Column(Integer)
    natural_product = Column(Integer)
    prodrug = Column(Integer)
    oral = Column(Boolean)
    parenteral = Column(Boolean)
    topical = Column(Boolean)
    inorganic_flag = Column(Integer)
    dosed_ingredient = Column(Boolean)
    
    properties = relationship("MoleculeProperty", back_populates="molecule", uselist=False, cascade="all, delete-orphan")
    synonyms = relationship("MoleculeSynonym", back_populates="molecule", cascade="all, delete-orphan")
    mechanisms = relationship("Mechanism", back_populates="molecule", cascade="all, delete-orphan")
    atc_classifications = relationship("MoleculeATC", back_populates="molecule", cascade="all, delete-orphan")
    cross_references = relationship("MoleculeCrossReference", back_populates="molecule", cascade="all, delete-orphan")

class MoleculeProperty(Base):
    __tablename__ = "molecule_properties"
    
    id = Column(Integer, primary_key=True)
    chembl_id = Column(String, ForeignKey("molecules.chembl_id"))
    molecular_weight = Column(Float)
    alogp = Column(Float)
    hba = Column(Integer)
    hbd = Column(Integer)
    psa = Column(Float)
    rtb = Column(Integer)
    
    # Additional properties
    aromatic_rings = Column(Integer)
    heavy_atoms = Column(Integer)
    mw_freebase = Column(Float)
    np_likeness_score = Column(Float)
    num_ro5_violations = Column(Integer)
    qed_weighted = Column(Float)
    ro3_pass = Column(String)
    
    molecule = relationship("Molecule", back_populates="properties")

class MoleculeSynonym(Base):
    __tablename__ = "molecule_synonyms"
    
    id = Column(Integer, primary_key=True)
    chembl_id = Column(String, ForeignKey("molecules.chembl_id"))
    synonym = Column(String)
    syn_type = Column(String)
    
    molecule = relationship("Molecule", back_populates="synonyms")

class Mechanism(Base):
    __tablename__ = "mechanisms"
    
    id = Column(Integer, primary_key=True)
    chembl_id = Column(String, ForeignKey("molecules.chembl_id"))
    mechanism_of_action = Column(String)
    target_name = Column(String)
    target_chembl_id = Column(String)
    action_type = Column(String)
    
    molecule = relationship("Molecule", back_populates="mechanisms")

class MoleculeATC(Base):
    __tablename__ = "molecule_atc"
    
    id = Column(Integer, primary_key=True)
    chembl_id = Column(String, ForeignKey("molecules.chembl_id"))
    level5 = Column(String)
    
    molecule = relationship("Molecule", back_populates="atc_classifications")

class MoleculeCrossReference(Base):
    __tablename__ = "molecule_cross_refs"
    
    id = Column(Integer, primary_key=True)
    chembl_id = Column(String, ForeignKey("molecules.chembl_id"))
    xref_src = Column(String)
    xref_id_val = Column(String)
    xref_name = Column(String)
    
    molecule = relationship("Molecule", back_populates="cross_references")

class SearchTerm(Base):
    __tablename__ = "search_terms"
    
    id = Column(Integer, primary_key=True)
    term = Column(String, unique=True, nullable=False)
    timestamp = Column(DateTime, default=None)

class SearchToMolecule(Base):
    __tablename__ = "search_to_molecule"
    
    search_id = Column(Integer, ForeignKey("search_terms.id"), primary_key=True)
    chembl_id = Column(String, ForeignKey("molecules.chembl_id"), primary_key=True)

def create_tables():
    """Create all tables in the database."""
    config.ensure_dir_exists()
    engine = create_engine(config.DB_URL)
    Base.metadata.create_all(engine)

def get_session() -> Session:
    """Get a new database session."""
    engine = create_engine(config.DB_URL)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

def drop_tables():
    """Drop all tables in the database."""
    engine = create_engine(config.DB_URL)
    Base.metadata.drop_all(engine)
