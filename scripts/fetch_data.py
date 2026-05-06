import requests
import pandas as pd
from datetime import datetime

# Codes ISO des 8 pays UEMOA
PAYS_UEMOA = {
    "BJ": "Bénin",
    "BF": "Burkina Faso",
    "CI": "Côte d'Ivoire",
    "GW": "Guinée-Bissau",
    "ML": "Mali",
    "NE": "Niger",
    "SN": "Sénégal",
    "TG": "Togo"
}

# ── 1. API FMI ───────────────────────────────────────────
def fetch_world_bank_extra(indicator_code, label, pays_codes):
    """Récupère des indicateurs supplémentaires via la Banque Mondiale"""
    pays_str = ";".join(pays_codes)
    url = (
        f"https://api.worldbank.org/v2/country/{pays_str}"
        f"/indicator/{indicator_code}"
        f"?format=json&per_page=100&mrv=6"
    )
    print(f"  → Appel Banque Mondiale : {indicator_code}...")
    response = requests.get(url, timeout=15)
    data = response.json()

    rows = []
    for entry in data[1] or []:
        if entry["value"] is not None:
            rows.append({
                "pays_code": entry["countryiso3code"],
                "pays_nom": entry["country"]["value"],
                "annee": int(entry["date"]),
                "valeur": entry["value"],
                "indicateur": label,
                "source": "Banque Mondiale"
            })
    return pd.DataFrame(rows)


# ── 2. API Banque Mondiale ───────────────────────────────
def fetch_world_bank(indicator_code, pays_codes):
    pays_str = ";".join(pays_codes)
    url = (
        f"https://api.worldbank.org/v2/country/{pays_str}"
        f"/indicator/{indicator_code}"
        f"?format=json&per_page=100&mrv=6"
    )
    print(f"  → Appel Banque Mondiale : {indicator_code}...")
    response = requests.get(url, timeout=15)
    data = response.json()

    rows = []
    for entry in data[1] or []:
        if entry["value"] is not None:
            rows.append({
                "pays_code": entry["countryiso3code"],
                "pays_nom": entry["country"]["value"],
                "annee": int(entry["date"]),
                "valeur": entry["value"],
                "indicateur": indicator_code,
                "source": "Banque Mondiale"
            })
    return pd.DataFrame(rows)


# ── 3. Orchestration principale ──────────────────────────
def update_all():
    pays_codes = list(PAYS_UEMOA.keys())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_data = []

    print(f"\n{'='*50}")
    print(f"  UEMOA DATA — Mise à jour : {timestamp}")
    print(f"{'='*50}\n")

    # Indicateurs FMI
    # Tous les indicateurs via Banque Mondiale
    wb_indicators = {
        "FP.CPI.TOTL.ZG":    "Inflation IPC (%)",
        "NY.GDP.MKTP.KD.ZG": "Croissance PIB (%)",
        "GC.DOD.TOTL.GD.ZS": "Dette publique / PIB (%)",
        "BN.CAB.XOKA.GD.ZS": "Balance courante / PIB (%)",
        "NY.GDP.MKTP.CD":     "PIB nominal (USD)"
    }
    for code, label in wb_indicators.items():
        try:
            df = fetch_world_bank_extra(code, label, pays_codes)
            all_data.append(df)
            print(f"  ✓ {label} — {len(df)} lignes")
        except Exception as e:
            print(f"  ✗ Erreur {code} : {e}")

    # Indicateurs Banque Mondiale
    wb_indicators = {
        "FP.CPI.TOTL.ZG": "Inflation IPC (%)",
        "NY.GDP.MKTP.KD.ZG": "Croissance PIB (%)"
    }
    for code in wb_indicators:
        try:
            df = fetch_world_bank(code, pays_codes)
            all_data.append(df)
            print(f"  ✓ {wb_indicators[code]} — {len(df)} lignes")
        except Exception as e:
            print(f"  ✗ Erreur Banque Mondiale {code} : {e}")

    # Consolidation
    final = pd.concat(all_data, ignore_index=True)
    final["updated_at"] = timestamp

    # Sauvegarde
    final.to_csv("data/uemoa_indicators.csv", index=False)

    print(f"\n{'='*50}")
    print(f"  ✓ {len(final)} lignes sauvegardées dans data/uemoa_indicators.csv")
    print(f"{'='*50}\n")

    return final


if __name__ == "__main__":
    update_all()