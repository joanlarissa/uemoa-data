import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()
engine = create_engine(os.getenv('DATABASE_URL'))

df = pd.read_csv('data/bceao_indicators.csv')
print(f'{len(df)} lignes lues depuis bceao_indicators.csv')

# Nettoyage des colonnes trop longues
df['libelle'] = df['libelle'].astype(str).str[:200]
df['indicateur'] = df['indicateur'].astype(str).str[:200]
df['source'] = df['source'].astype(str).str[:100]
df['pays_nom'] = df['pays_nom'].astype(str).str[:100]

# Garde uniquement les colonnes compatibles avec la table indicators
colonnes = ['pays_code', 'pays_nom', 'annee', 'valeur', 'indicateur', 'source', 'updated_at']
df_clean = df[colonnes].copy()

print(f'Colonnes : {list(df_clean.columns)}')
print(f'Aperçu :\n{df_clean.head(3)}')

with engine.connect() as conn:
    conn.execute(text("DELETE FROM indicators WHERE source LIKE '%BCEAO%'"))
    conn.commit()
    print('Anciennes données BCEAO supprimées')

df_clean.to_sql('indicators', engine, if_exists='append', index=False)
print(f'✓ {len(df_clean)} lignes BCEAO insérées en base')