import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import time
from fake_useragent import UserAgent
import numpy as np
import random
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse

class Scraper():
    def __init__(self):
        """Initialize the scraper with base URL."""
        self.base_url = 'https://listado.mercadolibre.com.co/'
        self.driver = None  # WebDriver starts as None

    def create_driver(self):
        """Creates a new WebDriver instance with improved anti-detection settings."""
        options = webdriver.ChromeOptions()

        if random.choice([True, False]):
            options.add_argument("--headless")

        #Incognito mode & bot evasion
        options.add_argument("--incognito")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # Rotate User-Agent (desktop only)
        ua = UserAgent()
        user_agent = ua.chrome
        print(f"🕵️ Using User-Agent: {user_agent}")
        options.add_argument(f"user-agent={user_agent}")

        # We launch WebDriver
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    def restart_driver(self):
        """Restarts the WebDriver to avoid detection."""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass 

        time.sleep(random.uniform(5, 10))  #Short pause before restart
        self.driver = self.create_driver()

    def encode_product_name(self, product_name):
        formatted_name = product_name.replace(" ", "-").lower()
        formatted_name = urllib.parse.quote(formatted_name)
        formatted_name = formatted_name.replace("/", "%2F").replace("\"", "%22")

        return formatted_name

    def close_popup(self):
        """Detects and closes the pop-up to avoid interference."""
        try:
            popup = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Por ahora no')]"))
            )
            popup.click()
            print("Pop-up closed!")
            time.sleep(2) 
            
        except Exception:
            print("⚠️ No pop-up detected or already closed.")

    def scraping(self, product_name, code):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                if self.driver is None or (retry_count % 5 == 0 and retry_count > 0):
                    print("Restarting WebDriver to avoid detection...")
                    self.restart_driver()
                
                cleaned_name = self.encode_product_name(product_name)
                url = f"{self.base_url}{cleaned_name}-{code}" if pd.notna(code) else f"{self.base_url}{cleaned_name}"
                print(f"Scraping: {url}")

                self.driver.get(url)
                time.sleep(random.uniform(5, 10))

                self.close_popup()

                #We wait until products load
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "li.ui-search-row__item"))
                )

                # We do as if we scroll to simulate human behavior
                for _ in range(random.randint(2, 5)):
                    scroll_amount = random.randint(300, 900)
                    self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                    time.sleep(random.uniform(2, 4))

                #We choose the first product
                try:
                    first_product = WebDriverWait(self.driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "li.ui-search-row__item div.ui-search-result a"))
                    )
                    first_product_url = first_product.get_attribute("href")
                    
                    print(f"Opening product page: {first_product_url}")

                    self.driver.execute_script("arguments[0].scrollIntoView();", first_product)
                    time.sleep(random.uniform(2, 4))
                    first_product.click()
                    time.sleep(random.uniform(5, 12))
                    
                except Exception as e:
                    print(f"No clickable product found: {e}. Retrying...")
                    retry_count += 1
                    continue

                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, 'ui-pdp-title'))
                )

                soup = BeautifulSoup(self.driver.page_source, 'html.parser')

                try:
                    title = soup.find('h1', class_='ui-pdp-title').text.strip()
                except AttributeError:
                    print("⚠️ Could not find title, retrying...")
                    retry_count += 1
                    continue

                #Product description
                description_section = soup.find('p', class_='ui-pdp-description__content')
                definicion = description_section.text.strip().replace("\n", ", ") if description_section else "No description found"

                #Product characteristics
                highlighted_specs_section = soup.find('div', id='highlighted_specs_features')
                highlighted_specs = ', '.join([spec.text.strip().replace("\n", ", ") for spec in highlighted_specs_section.find_all('div')]) if highlighted_specs_section else "No highlighted specs found"

                table_specs = {"Características principales": "", "Otros": ""}
                table_specs_sections = soup.find_all('div', class_='ui-vpp-striped-specs')
                
                for section in table_specs_sections:
                    header = section.find('h3', class_='ui-vpp-striped-specs__header')
                    if header:
                        header_text = header.text.strip()
                        table_rows = section.find_all('tr')
                        table_specs[header_text] = ', '.join([' '.join([cell.text.strip() for cell in row.find_all(['th', 'td'])]) for row in table_rows])

                definicion_final = definicion + " " + highlighted_specs
                caracteristicas = table_specs["Características principales"] + " " + table_specs["Otros"]

                print(f"\Product Found: {title}")
                return [{
                    "title": title.upper(),
                    "definicion": definicion_final,
                    "caracteristicas": caracteristicas
                }]
                
            except Exception as e:
                print(f"Error occurred: {e}")
                retry_count += 1
                self.restart_driver()

                if retry_count < max_retries:
                    print(f"Retrying ({retry_count}/{max_retries})...")
                    time.sleep(random.uniform(30, 90))
                else:
                    print(f"Max retries reached for {product_name}. Skipping...")
                    return None

    def scrap_df(self, df, original_df):
        """Scrapes a DataFrame of product names and updates only the corresponding rows."""
        
        # We start WebDriver once per batch to prevent crashes
        if self.driver is None:
            self.restart_driver()

        for i in range(len(df)):
            original_index = df.index[i] 

            print(f"📦 Processing product {i + 1}/{len(df)} (Original Index: {original_index})")

            if (i + 1) % 5 == 0 and i != 0:
                print("Restarting WebDriver to avoid detection...")
                self.restart_driver()
                time.sleep(random.uniform(30, 60))

            try:
                product_name = df.loc[original_index, "Nombre"]
                code = df.loc[original_index, "Referencia"]
            except KeyError as e:
                print(f"KeyError: {e} - Skipping row {original_index}")
                continue

            data = self.scraping(product_name, code)

            if data:
                scraped_data = data[0]
                original_df.at[original_index, "Descripción"] = scraped_data["definicion"] + " " + scraped_data["caracteristicas"]
            else:
                original_df.at[original_index, "Descripción"] = np.nan

            time.sleep(random.uniform(10, 30))  # Add delay between scrapes

        #We close WebDriver after processing batch
        self.driver.quit()
        self.driver = None 

        return original_df  
    
if __name__ == "__main__":

    #We start by reading the csv file
    data = pd.read_csv("../../data/inventario_ferritienda.csv", sep=";", encoding="latin1")
    data = data.drop(data.columns[[0, 1, 2, 3]], axis=1)
    
    # Update column names
    data.columns = [
    "Nombre", 
    "Código del producto o servicio", 
    "Referencia", 
    "Unidad de medida", 
    "Categoria", 
    "Descripcion", 
    "Costo inicial", 
    "Precio base", 
    "Impuesto", 
    "Precio total", 
    "Precio general", 
    "Precio lista general 2023", 
    "Código cuenta contable", 
    "Cuenta contable", 
    "Código cuenta de inventario", 
    "Cuenta de inventario", 
    "Código cuenta de costo de venta", 
    "Cuenta de costo de venta", 
    "Código de barras 2", 
    "Código de barras 3", 
    "Código de barras"
    ]
    data = data.drop(columns=[ "Código del producto o servicio", "Unidad de medida", 
    "Costo inicial", 
    "Precio base", 
    "Impuesto", 
    "Precio total", 
    "Precio general", 
    "Precio lista general 2023", 
    "Código cuenta contable", 
    "Cuenta contable", 
    "Código cuenta de inventario", 
    "Cuenta de inventario", 
    "Código cuenta de costo de venta", 
    "Cuenta de costo de venta", 
    "Código de barras 2", 
    "Código de barras 3", 
    "Código de barras" ])
    
    data["Marca"] = data["Nombre"].str.split().str[-1]
    
    # TRUPER PRODUCTS 
    truper_products = data[data["Marca"] == "TRUPER"].copy()
    truper_products['Marca'] = truper_products['Marca'] + " " + truper_products['Descripcion'].str.findall(r'\d+').str.join(" ")
    
    # truper_electric_tools = truper_products[
    # (truper_products["Categoría"] == "HERRAMIENTA ELECTRICA") | 
    # (truper_products["Categoría"] == "HERRAMIENTA MANUAL")
    # ]
    # sample_truper_electric_tools = truper_electric_tools.sample(100, random_state=42)
    # sample_truper_electric_tools.head()
    
    # sample_truper_electric_tools["Definicion"] = np.nan
    # sample_truper_electric_tools["Caracteristicas"] = np.nan
    
    # sample_truper_electric_tools_ = sample_truper_electric_tools.sample(10)
    already_sampled = pd.read_csv("sample_electric_truper_products.csv", sep=";", encoding="utf-8")
    already_sampled_refs = already_sampled["Referencia"].unique()
    truper_products_to_scrape = truper_products[~truper_products["Referencia"].isin(already_sampled_refs)]
    
    truper_products_to_scrape = truper_products_to_scrape.reset_index(drop=True)
    first_block = truper_products_to_scrape.iloc[:100].copy()  # We take the first 100 products to scrape
    s = Scraper()
    
    batch_size = 5  # ✅ Process 5 products at a time

    for start in range(0, len(truper_products_to_scrape), batch_size):
        end = min(start + batch_size, len(truper_products_to_scrape))
        print(f"\n🚀 Processing products {start} to {end}...\n")

        batch_df = truper_products_to_scrape.iloc[start:end]
        # We scrape batch and update the original DataFrame
        truper_products_to_scrape = s.scrap_df(batch_df, truper_products_to_scrape)

        delay = np.random.uniform(30, 90)
        print(f"⏳ Waiting {delay:.2f} seconds before next batch...\n")
        time.sleep(delay)

    print("✅ Scraping completed for all products!")
    truper_products_to_scrape.to_csv("data/scraped_electric_truper_data_rest.csv", sep=";", index=False)
