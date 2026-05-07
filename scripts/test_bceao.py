from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd

options = webdriver.ChromeOptions()
options.add_argument('--headless')
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

driver.get('https://edenpub.bceao.int/index.php')
time.sleep(3)

# Clic sur IPC MENSUEL
links = driver.find_elements(By.TAG_NAME, 'a')
for link in links:
    if 'MENSUEL' in link.text and 'CONSOMMATION' in link.text:
        link.click()
        time.sleep(4)
        break

# Clique sur "Tout sélectionner"
tout_select = driver.find_element(By.LINK_TEXT, 'Tout sélectionner')
tout_select.click()
time.sleep(1)
print('Tous les pays sélectionnés ✓')

# Remplis la période
Select(driver.find_element(By.NAME, 'mois_debut')).select_by_value('01')
Select(driver.find_element(By.NAME, 'annee_debut')).select_by_value('2023')
Select(driver.find_element(By.NAME, 'mois_fin')).select_by_value('12')
Select(driver.find_element(By.NAME, 'annee_fin')).select_by_value('2025')
print('Période remplie ✓')

# Sans méta-données est déjà sélectionné
# Clique sur Afficher
driver.find_element(By.XPATH, "//input[@value='Afficher'] | //button[contains(text(),'Afficher')]").click()
time.sleep(5)
print('Formulaire soumis ✓')

# Extrait les tables
tables = driver.find_elements(By.TAG_NAME, 'table')
print(f'{len(tables)} tables trouvées')
for i, t in enumerate(tables):
    txt = t.text.strip()
    if txt and len(txt) > 100:
        print(f'\n--- Table {i+1} ---')
        print(txt[:1000])

driver.quit()