from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func

from database import Base


class CultureRecord(Base):
    """A single tissue-culture experiment / observation entry."""

    __tablename__ = "culture_records"

    id = Column(Integer, primary_key=True, index=True)
    species = Column(String, index=True, nullable=False)
    explant_type = Column(String, nullable=False)
    treatment = Column(String, nullable=True)          # e.g. "BAP 2mg/L"
    shoots_per_explant = Column(Float, nullable=True)
    contamination_status = Column(String, nullable=True)  # e.g. "Low", "Medium", "High"
    rooting_percent = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Disease(Base):
    """A plant disease / pathogen reference entry with symptoms and management notes."""

    __tablename__ = "diseases"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)          # e.g. "Panama disease"
    pathogen = Column(String, nullable=True)                   # e.g. "Fusarium oxysporum f. sp. cubense"
    pathogen_type = Column(String, nullable=True)              # e.g. "Fungus", "Bacteria", "Virus", "Nematode"
    host_species = Column(String, nullable=True)                # e.g. "Banana (Musa spp.)"
    symptoms = Column(String, nullable=False)                    # free-text, searchable
    management = Column(String, nullable=True)                  # control/management notes
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PlantProfile(Base):
    """An AI-generated, cached reference profile for a plant species."""

    __tablename__ = "plant_profiles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, unique=True, nullable=False)  # e.g. "Musa acuminata (Banana)"
    taxonomy = Column(Text, nullable=True)
    morphology = Column(Text, nullable=True)
    anatomy = Column(Text, nullable=True)
    biochemistry = Column(Text, nullable=True)
    molecular_biology = Column(Text, nullable=True)
    physiology = Column(Text, nullable=True)
    economic_importance = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())