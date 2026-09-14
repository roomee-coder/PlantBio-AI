from typing import List

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import models
import schemas
from database import Base, engine, get_db
from ai_service import ask_plant_ai, analyze_culture_image, diagnose_symptoms, autofill_disease, generate_plant_profile

# Create tables on startup (fine for SQLite/dev; use Alembic migrations later)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="PlantBio AI Backend", version="0.1.0")

# Allow the frontend (served from another origin/port) to call this API.
# Tighten allow_origins to your real frontend URL before deploying.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"status": "ok", "message": "PlantBio AI backend is running"}


@app.post("/records", response_model=schemas.CultureRecordOut)
def create_record(record: schemas.CultureRecordCreate, db: Session = Depends(get_db)):
    db_record = models.CultureRecord(**record.model_dump())
    db.add(db_record)
    db.commit()
    db.refresh(db_record)
    return db_record


@app.get("/records", response_model=List[schemas.CultureRecordOut])
def list_records(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.CultureRecord).offset(skip).limit(limit).all()


@app.get("/records/{record_id}", response_model=schemas.CultureRecordOut)
def get_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.CultureRecord).filter(models.CultureRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    return record


@app.put("/records/{record_id}", response_model=schemas.CultureRecordOut)
def update_record(record_id: int, updates: schemas.CultureRecordUpdate, db: Session = Depends(get_db)):
    record = db.query(models.CultureRecord).filter(models.CultureRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(record, field, value)

    db.commit()
    db.refresh(record)
    return record


@app.delete("/records/{record_id}")
def delete_record(record_id: int, db: Session = Depends(get_db)):
    record = db.query(models.CultureRecord).filter(models.CultureRecord.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")

    db.delete(record)
    db.commit()
    return {"detail": f"Record {record_id} deleted"}


@app.post("/ask", response_model=schemas.AskResponse)
def ask_ai(request: schemas.AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        answer = ask_plant_ai(request.question)
    except RuntimeError as e:
        # Raised when GEMINI_API_KEY is missing
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI request failed: {e}")

    return schemas.AskResponse(answer=answer)


# ---------------------------------------------------------------------------
# Plant Pathology module — disease / symptom reference records
# ---------------------------------------------------------------------------

@app.post("/diseases", response_model=schemas.DiseaseOut)
def create_disease(disease: schemas.DiseaseCreate, db: Session = Depends(get_db)):
    db_disease = models.Disease(**disease.model_dump())
    db.add(db_disease)
    db.commit()
    db.refresh(db_disease)
    return db_disease


@app.get("/diseases", response_model=List[schemas.DiseaseOut])
def list_diseases(
    skip: int = 0,
    limit: int = 100,
    symptom: str = None,
    db: Session = Depends(get_db),
):
    """List diseases, optionally filtering by a symptom keyword (case-insensitive)."""
    query = db.query(models.Disease)
    if symptom:
        query = query.filter(models.Disease.symptoms.ilike(f"%{symptom}%"))
    return query.offset(skip).limit(limit).all()


@app.get("/diseases/{disease_id}", response_model=schemas.DiseaseOut)
def get_disease(disease_id: int, db: Session = Depends(get_db)):
    disease = db.query(models.Disease).filter(models.Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")
    return disease


@app.put("/diseases/{disease_id}", response_model=schemas.DiseaseOut)
def update_disease(disease_id: int, updates: schemas.DiseaseUpdate, db: Session = Depends(get_db)):
    disease = db.query(models.Disease).filter(models.Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")

    for field, value in updates.model_dump(exclude_unset=True).items():
        setattr(disease, field, value)

    db.commit()
    db.refresh(disease)
    return disease


@app.delete("/diseases/{disease_id}")
def delete_disease(disease_id: int, db: Session = Depends(get_db)):
    disease = db.query(models.Disease).filter(models.Disease.id == disease_id).first()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found")

    db.delete(disease)
    db.commit()
    return {"detail": f"Disease {disease_id} deleted"}


# ---------------------------------------------------------------------------
# Real image analysis — send an uploaded culture photo to Gemini vision
# ---------------------------------------------------------------------------

MAX_IMAGE_BYTES = 10 * 1024 * 1024  # 10 MB, matches the frontend's stated limit
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}


@app.post("/analyze-image", response_model=schemas.ImageAnalysisResponse)
async def analyze_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Use PNG, JPG, or WEBP.",
        )

    image_bytes = await file.read()
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Image is larger than 10 MB.")

    try:
        analysis = analyze_culture_image(image_bytes, file.content_type)
    except RuntimeError as e:
        # Raised when GEMINI_API_KEY is missing
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI image analysis failed: {e}")

    return schemas.ImageAnalysisResponse(analysis=analysis)


# ---------------------------------------------------------------------------
# Pathology + AI integration — symptom-based diagnosis and record autofill
# ---------------------------------------------------------------------------

@app.post("/diagnose", response_model=schemas.DiagnoseResponse)
def diagnose(request: schemas.DiagnoseRequest, db: Session = Depends(get_db)):
    if not request.symptoms.strip():
        raise HTTPException(status_code=400, detail="Symptoms cannot be empty")

    # Look for existing disease records whose symptoms text overlaps with
    # words from the user's description, to give the AI real reference context.
    words = {w.strip(",.;:") for w in request.symptoms.lower().split() if len(w) > 3}
    query = db.query(models.Disease)
    if words:
        from sqlalchemy import or_
        conditions = [models.Disease.symptoms.ilike(f"%{w}%") for w in words]
        query = query.filter(or_(*conditions))
    matches = query.limit(5).all()

    matched_dicts = [
        {
            "name": m.name,
            "pathogen": m.pathogen,
            "pathogen_type": m.pathogen_type,
            "symptoms": m.symptoms,
            "management": m.management,
        }
        for m in matches
    ]

    try:
        answer = diagnose_symptoms(request.symptoms, matched_dicts)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI diagnosis failed: {e}")

    return schemas.DiagnoseResponse(answer=answer, matches=matches)


@app.post("/autofill-disease", response_model=schemas.AutofillDiseaseResponse)
def autofill_disease_endpoint(request: schemas.AutofillDiseaseRequest):
    if not request.name.strip():
        raise HTTPException(status_code=400, detail="Disease name cannot be empty")

    try:
        fields = autofill_disease(request.name)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI autofill failed: {e}")

    return schemas.AutofillDiseaseResponse(**fields)

# ---------------------------------------------------------------------------
# Plant Library — AI-generated, database-cached species reference profiles
# ---------------------------------------------------------------------------

@app.post("/plant-library/search", response_model=schemas.PlantProfileOut)
def search_plant_library(request: schemas.PlantSearchRequest, db: Session = Depends(get_db)):
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Plant name cannot be empty")

    # Serve from the cache if we've already generated this profile (case-insensitive).
    existing = db.query(models.PlantProfile).filter(models.PlantProfile.name.ilike(name)).first()
    if existing:
        return existing

    try:
        fields = generate_plant_profile(name)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI plant profile generation failed: {e}")

    profile = models.PlantProfile(name=name, **fields)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@app.get("/plant-library", response_model=List[schemas.PlantProfileOut])
def list_plant_library(db: Session = Depends(get_db)):
    return db.query(models.PlantProfile).order_by(models.PlantProfile.name).all()


@app.get("/plant-library/{profile_id}", response_model=schemas.PlantProfileOut)
def get_plant_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(models.PlantProfile).filter(models.PlantProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Plant profile not found")
    return profile


@app.delete("/plant-library/{profile_id}")
def delete_plant_profile(profile_id: int, db: Session = Depends(get_db)):
    profile = db.query(models.PlantProfile).filter(models.PlantProfile.id == profile_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Plant profile not found")
    db.delete(profile)
    db.commit()
    return {"detail": f"Plant profile {profile_id} deleted"}