from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time
import sys
from datetime import datetime
from dateutil.relativedelta import relativedelta

# Mapping pays BCEAO → ISO2
PAYS_MAP = {
    "BENIN": "BJ", "BURKINA FASO": "BF", "COTE D'IVOIRE": "CI",
    "GUINEE BISSAU": "GW", "MALI": "ML", "NIGER": "NE",
    "SENEGAL": "SN", "TOGO": "TG", "ENSEMBLE UEMOA": "UEMOA"
}

# Indicateurs disponibles sur edenpub
INDICATEURS = {
    "IPC_MENSUEL":          "INDICE DES PRIX A LA CONSOMMATION MENSUEL",
    "INFLATION_GLISSEMENT": "TAUX D'INFATION EN GLISSEMENT ANNUEL",
    "INFLATION_MOYENNE":    "TAUX D'INFATION EN MOYENNE ANNUELLE",
    "PIB_CONSTANT":         "PIB ET SES EMPLOIS A PRIX CONSTANT",
    "PIB_NOMINAL":          "PIB ET SES EMPLOIS EN VALEUR NOMINALE",
    "INDICATEURS_MACRO":    "PRINCIPAUX INDICATEURS MACROECONOMIQUES",
}

def init_driver(headless=True):
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver


def scrape_indicateur(driver, nom_indicateur, mois_debut, annee_debut, mois_fin, annee_fin):
    """Scrape un indicateur depuis edenpub.bceao.int"""
    rows = []

    try:
        driver.get('https://edenpub.bceao.int/index.php')
        time.sleep(3)

        # Clic sur l'indicateur voulu
        links = driver.find_elements(By.TAG_NAME, 'a')
        found = False
        for link in links:
            if nom_indicateur in link.text.upper():
                link.click()
                time.sleep(4)
                found = True
                break

        if not found:
            print(f'  ✗ Indicateur non trouvé : {nom_indicateur}')
            return rows

        # Sélectionne tous les pays
        try:
            tout = driver.find_element(By.LINK_TEXT, 'Tout sélectionner')
            tout.click()
            time.sleep(1)
        except:
            # Coche chaque pays manuellement
            checkboxes = driver.find_elements(By.CSS_SELECTOR, 'input[type=checkbox]')
            for cb in checkboxes:
                if not cb.is_selected():
                    cb.click()

        # Remplis la période
        Select(driver.find_element(By.NAME, 'mois_debut')).select_by_value(mois_debut)
        Select(driver.find_element(By.NAME, 'annee_debut')).select_by_value(annee_debut)
        Select(driver.find_element(By.NAME, 'mois_fin')).select_by_value(mois_fin)
        Select(driver.find_element(By.NAME, 'annee_fin')).select_by_value(annee_fin)

        # Sans méta-données
        try:
            sans_meta = driver.find_element(By.XPATH, "//input[@value='0' and @name='metadonnees'] | //input[contains(@id,'sans')]")
            if not sans_meta.is_selected():
                sans_meta.click()
        except:
            pass

        # Clique Afficher
        try:
            afficher = driver.find_element(By.XPATH, "//input[@value='Afficher']")
            afficher.click()
        except:
            afficher = driver.find_element(By.XPATH, "//button[contains(text(),'Afficher')]")
            afficher.click()

        time.sleep(5)

        # Parse les tableaux avec BeautifulSoup
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tables = soup.find_all('table')

        pays_courant = "INCONNU"

        for table in tables:
            rows_html = table.find_all('tr')
            if not rows_html:
                continue

            # Détecte le nom du pays dans les lignes précédentes
            table_text = table.get_text()

            # Identifie le pays
            for pays_nom, pays_code in PAYS_MAP.items():
                if pays_nom in table_text.upper():
                    pays_courant = pays_code
                    break

            # Extrait les colonnes (mois)
            header_row = None
            for row in rows_html:
                cells = row.find_all(['th', 'td'])
                texts = [c.get_text(strip=True) for c in cells]
                # Cherche la ligne d'en-tête avec les mois
                if any('2023' in t or '2024' in t or '2025' in t for t in texts):
                    header_row = texts
                    break

            if not header_row:
                continue

            # Extrait les données
            for row in rows_html:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                texts = [c.get_text(strip=True) for c in cells]

                libelle = texts[1] if len(texts) > 1 else texts[0]

                # Pour chaque colonne de date
                for i, col_header in enumerate(header_row):
                    if len(col_header) == 7 and col_header[3:].isdigit():
                        # Format MOISANNEE ex: JAN2023
                        mois_str = col_header[:3]
                        annee_str = col_header[3:]
                        mois_map = {
                            'JAN': '01', 'FEV': '02', 'MAR': '03', 'AVR': '04',
                            'MAI': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                            'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
                        }
                        mois_num = mois_map.get(mois_str, '01')

                        if i < len(texts):
                            try:
                                valeur = float(texts[i].replace(',', '.').replace(' ', ''))
                                rows.append({
                                    "pays_code": pays_courant,
                                    "pays_nom": [k for k, v in PAYS_MAP.items() if v == pays_courant][0] if pays_courant != "UEMOA" else "Zone UEMOA",
                                    "annee": int(annee_str),
                                    "mois": int(mois_num),
                                    "date": f"{annee_str}-{mois_num}-01",
                                    "valeur": valeur,
                                    "libelle": libelle,
                                    "indicateur": nom_indicateur,
                                    "source": "BCEAO - edenpub"
                                })
                            except:
                                continue

    except Exception as e:
        print(f'  ✗ Erreur scraping {nom_indicateur} : {e}')

    return rows


def fetch_bceao(date_debut=None, date_fin=None):
    """
    Scrape dynamiquement les données BCEAO depuis edenpub.bceao.int

    Usage :
        python scripts/fetch_bceao.py 2023-01 2025-12
        python scripts/fetch_bceao.py
    """
    if not date_debut:
        date_debut = (datetime.now() - relativedelta(years=3)).strftime("%Y-%m")
    if not date_fin:
        date_fin = (datetime.now() - relativedelta(months=2)).strftime("%Y-%m")

    mois_debut = date_debut[5:7]
    annee_debut = date_debut[:4]
    mois_fin = date_fin[5:7]
    annee_fin = date_fin[:4]

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    all_rows = []

    print(f"\n{'='*50}")
    print(f"  BCEAO edenpub — Selenium Scraper")
    print(f"  Plage       : {date_debut} → {date_fin}")
    print(f"  Mise à jour : {timestamp}")
    print(f"{'='*50}\n")

    driver = init_driver(headless=True)

    try:
        # Indicateurs à scraper
        indicateurs_cibles = [
            "INDICE DES PRIX A LA CONSOMMATION MENSUEL",
            "TAUX D'INFATION EN GLISSEMENT ANNUEL",
            "PRINCIPAUX INDICATEURS MACROECONOMIQUES",
        ]

        for indicateur in indicateurs_cibles:
            print(f"  → Scraping : {indicateur}...")
            rows = scrape_indicateur(
                driver, indicateur,
                mois_debut, annee_debut,
                mois_fin, annee_fin
            )
            all_rows.extend(rows)
            print(f"  ✓ {len(rows)} lignes extraites")

    finally:
        driver.quit()

    if not all_rows:
        print("  ✗ Aucune donnée extraite")
        return pd.DataFrame()

    df = pd.DataFrame(all_rows)
    df["updated_at"] = timestamp
    df.to_csv("data/bceao_indicators.csv", index=False)

    print(f"\n{'='*50}")
    print(f"  ✓ {len(df)} lignes BCEAO sauvegardées")
    print(f"{'='*50}\n")

    return df


if __name__ == "__main__":
    if len(sys.argv) == 3:
        fetch_bceao(sys.argv[1], sys.argv[2])
    else:
        fetch_bceao()