# PlantBio AI

A full-stack plant biotechnology platform combining a tissue-culture/pathology
database, real AI assistance (Google Gemini), and a set of lab calculators —
built as a learning project while studying Plant Biotechnology.

## Features

- **AI Research Assistant** — ask plant biotechnology questions, answered by Gemini
- **AI Image Analysis** — upload a culture/plant photo for an AI-generated visual assessment
- **Research Lab** — log and browse tissue-culture experiment records (FastAPI + SQLite)
- **Plant Pathology** — disease/symptom reference database, symptom search, and an AI
  diagnosis tool that combines your saved records with Gemini's knowledge
- **AI Autofill** — generate disease reference fields (pathogen, management, etc.) from just a name
- **Plant Library** — search any plant by name for an AI-generated profile
  (taxonomy, morphology, anatomy, biochemistry, molecular biology, physiology,
  economic importance) — cached in the database after the first search
- **Molecular Biology / Lab Calculators** — primer Tm/GC%, reverse complement,
  DNA→protein translation, restriction site finder, dilution, molarity, PCR
  master mix, buffer prep, and agarose gel calculators (all client-side)

## Tech stack

- **Frontend:** HTML, CSS, vanilla JavaScript (no framework/build step)
- **Backend:** Python, FastAPI, SQLAlchemy, SQLite
- **AI:** Google Gemini API (`google-genai`)

## Project structure

```
.
├── backend/
│   ├── main.py            # FastAPI app and all API routes
│   ├── models.py          # SQLAlchemy database models
│   ├── schemas.py         # Pydantic request/response schemas
│   ├── database.py        # DB engine/session setup
│   ├── ai_service.py      # Gemini API calls (chat, image analysis, diagnosis, etc.)
│   ├── requirements.txt
│   └── .env.example       # Copy to .env and add your own Gemini key
└── frontend/
    ├── index.html
    ├── style.css
    └── script.js
```

## Running locally

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env         # then paste in your own GEMINI_API_KEY
uvicorn main:app --reload
```

The API will be live at `http://127.0.0.1:8000`, with interactive docs at
`http://127.0.0.1:8000/docs`.

### Frontend

Just open `frontend/index.html` in a browser — no build step needed. Make
sure the backend is running first, since the frontend calls it directly.

## Getting a free Gemini API key

1. Go to [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
2. Sign in with a Google account and create a key
3. Paste it into `backend/.env` as `GEMINI_API_KEY=...`

No credit card is required for the free tier.

## Notes

- This is a learning/portfolio project, not a clinical or diagnostic tool —
  AI-generated content (diagnoses, plant profiles, image analysis) should
  always be verified against primary literature or a domain expert.
- SQLite is used for simplicity; a production deployment would typically
  swap this for PostgreSQL.