from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CultureRecordBase(BaseModel):
    species: str
    explant_type: str
    treatment: Optional[str] = None
    shoots_per_explant: Optional[float] = None
    contamination_status: Optional[str] = None
    rooting_percent: Optional[float] = None
    notes: Optional[str] = None


class CultureRecordCreate(CultureRecordBase):
    pass


class CultureRecordUpdate(BaseModel):
    species: Optional[str] = None
    explant_type: Optional[str] = None
    treatment: Optional[str] = None
    shoots_per_explant: Optional[float] = None
    contamination_status: Optional[str] = None
    rooting_percent: Optional[float] = None
    notes: Optional[str] = None


class CultureRecordOut(CultureRecordBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AskRequest(BaseModel):
    question: str


class AskResponse(BaseModel):
    answer: str


class ImageAnalysisResponse(BaseModel):
    analysis: str


class DiseaseBase(BaseModel):
    name: str
    pathogen: Optional[str] = None
    pathogen_type: Optional[str] = None
    host_species: Optional[str] = None
    symptoms: str
    management: Optional[str] = None
    notes: Optional[str] = None


class DiseaseCreate(DiseaseBase):
    pass


class DiseaseUpdate(BaseModel):
    name: Optional[str] = None
    pathogen: Optional[str] = None
    pathogen_type: Optional[str] = None
    host_species: Optional[str] = None
    symptoms: Optional[str] = None
    management: Optional[str] = None
    notes: Optional[str] = None


class DiseaseOut(DiseaseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DiagnoseRequest(BaseModel):
    symptoms: str


class DiagnoseResponse(BaseModel):
    answer: str
    matches: list[DiseaseOut]


class AutofillDiseaseRequest(BaseModel):
    name: str


class AutofillDiseaseResponse(BaseModel):
    pathogen: Optional[str] = None
    pathogen_type: Optional[str] = None
    host_species: Optional[str] = None
    symptoms: Optional[str] = None
    management: Optional[str] = None
    notes: Optional[str] = None


class PlantSearchRequest(BaseModel):
    name: str


class PlantProfileOut(BaseModel):
    id: int
    name: str
    taxonomy: Optional[str] = None
    morphology: Optional[str] = None
    anatomy: Optional[str] = None
    biochemistry: Optional[str] = None
    molecular_biology: Optional[str] = None
    physiology: Optional[str] = None
    economic_importance: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
