from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import pandas as pd

# Configurer le navigateur
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # Mode sans affichage
driver = webdriver.Chrome(options=options)

# URL du site
URL = "https://www.exemple-bricolage.com/catalogue"
driver.get(URL)

# Attendre que les éléments se chargent
time.sleep(5)

# Extraire les données
produits = []
items = driver.find_elements(By.CLASS_NAME, "product-item")

for item in items:
    nom = item.find_element(By.CLASS_NAME, "product-name").text.strip()
    prix = item.find_element(By.CLASS_NAME, "price").text.strip()
    description = item.find_element(By.CLASS_NAME, "description").text.strip()

    produits.append({"Nom": nom, "Prix": prix, "Description": description})

# Fermer le navigateur
driver.quit()

# Convertir en DataFrame et sauvegarder
df = pd.DataFrame(produits)
df.to_csv("../data/scraped_products.csv", index=False)

print("✅ Données scrappées et enregistrées !")


# Charger les datasets
df_inventaire = pd.read_csv("../data/inventario_ferritienda.csv")
df_scraped = pd.read_csv("../data/scraped_products.csv")

# Fusionner les deux datasets
df_merged = pd.concat([df_inventaire, df_scraped], ignore_index=True)

# Sauvegarder le nouveau dataset
df_merged.to_csv("../data/inventario_ferritienda.csv", index=False)

print("✅ Données fusionnées avec succès !")