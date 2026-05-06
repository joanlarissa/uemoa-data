import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Chargement des variables d'environnement
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def load_csv_to_db():
    # Connexion à la base de données
    print("\n" + "="*50)
    print("  UEMOA DATA — Chargement en base de données")
    print("="*50 + "\n")

    engine = create_engine(DATABASE_URL)

    # Lecture du CSV
    df = pd.read_csv("data/uemoa_indicators.csv")
    print(f"  → {len(df)} lignes lues depuis le CSV")

    # Chargement dans PostgreSQL
    with engine.connect() as conn:
        # Supprime les anciennes données avant d'insérer
        conn.execute(text("DELETE FROM indicators"))
        conn.commit()
        print("  → Anciennes données supprimées")

    # Insertion des nouvelles données
    df.to_sql(
        "indicators",
        engine,
        if_exists="append",
        index=False
    )

    print(f"  ✓ {len(df)} lignes insérées dans PostgreSQL")
    print("\n" + "="*50)

    # Vérification
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM indicators"))
        count = result.fetchone()[0]
        print(f"  ✓ Vérification : {count} lignes en base")
    print("="*50 + "\n")

if __name__ == "__main__":
    load_csv_to_db()