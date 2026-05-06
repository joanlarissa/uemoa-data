from fastapi import FastAPI, Query
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from typing import Optional
import os

# Chargement des variables d'environnement
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

app = FastAPI(
    title="UEMOA DATA API",
    description="API publique de données macro-économiques pour la zone UEMOA",
    version="1.0.0"
)

# ── 1. Endpoint racine ───────────────────────────────────
@app.get("/")
def root():
    return {
        "projet": "UEMOA DATA",
        "version": "1.0.0",
        "description": "API macro-économique UEMOA",
        "endpoints": ["/indicators", "/countries", "/data"]
    }

# ── 2. Liste des indicateurs disponibles ─────────────────
@app.get("/indicators")
def get_indicators():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT DISTINCT indicateur, source FROM indicators ORDER BY indicateur"
        ))
        rows = result.fetchall()
    return {
        "count": len(rows),
        "indicators": [{"indicateur": r[0], "source": r[1]} for r in rows]
    }

# ── 3. Liste des pays disponibles ────────────────────────
@app.get("/countries")
def get_countries():
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT DISTINCT pays_code, pays_nom FROM indicators ORDER BY pays_nom"
        ))
        rows = result.fetchall()
    return {
        "count": len(rows),
        "countries": [{"code": r[0], "nom": r[1]} for r in rows]
    }

# ── 4. Données filtrables ────────────────────────────────
@app.get("/data")
def get_data(
    pays: Optional[str] = Query(None, description="Code ISO du pays ex: BJ"),
    indicateur: Optional[str] = Query(None, description="Nom de l'indicateur"),
    annee: Optional[int] = Query(None, description="Année ex: 2023")
):
    query = "SELECT * FROM indicators WHERE 1=1"
    params = {}

    if pays:
        query += " AND pays_code = :pays"
        params["pays"] = pays
    if indicateur:
        query += " AND indicateur = :indicateur"
        params["indicateur"] = indicateur
    if annee:
        query += " AND annee = :annee"
        params["annee"] = annee

    query += " ORDER BY pays_nom, annee"

    with engine.connect() as conn:
        result = conn.execute(text(query), params)
        rows = result.fetchall()
        cols = result.keys()

    return {
        "count": len(rows),
        "data": [dict(zip(cols, row)) for row in rows]
    }

# ── 5. Données par pays ──────────────────────────────────
@app.get("/countries/{pays_code}")
def get_country_data(pays_code: str):
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT * FROM indicators WHERE pays_code = :code ORDER BY indicateur, annee"
        ), {"code": pays_code.upper()})
        rows = result.fetchall()
        cols = result.keys()

    if not rows:
        return {"error": f"Pays '{pays_code}' non trouvé"}

    return {
        "pays": pays_code.upper(),
        "count": len(rows),
        "data": [dict(zip(cols, row)) for row in rows]
    }