from dotenv import load_dotenv
import requests
import base64
import os
import pandas as pd
from IPython.display import display, HTML  

load_dotenv()


ALEGRA_API_TOKEN = os.getenv("ALEGRA_API_TOKEN")
ALEGRA_EMAIL = os.getenv("ALEGRA_EMAIL")

if not ALEGRA_API_TOKEN or not ALEGRA_EMAIL:
    raise ValueError("API credentials not found. Make sure to set them in the .env file.")

URL = "https://api.alegra.com/api/v1/items"

def get_auth_headers():
    sample_string_bytes = f"{ALEGRA_EMAIL}:{ALEGRA_API_TOKEN}".encode("ascii")
    base64_bytes = base64.b64encode(sample_string_bytes)
    base64_string = base64_bytes.decode("ascii")

    headers = {
        "accept": "application/json",
        "authorization": f"Basic {base64_string}",
        "content-type": "application/json", 
    }
    return headers

"""Function to get all itemp on the inventory"""
def fetch_all_data():
    headers = get_auth_headers()
    response = requests.get(URL, headers=headers)
    response.json()
    
    if response.status_code == 200:
        try:
            return response.json()  # Return parsed JSON data
        except ValueError:
            print("Invalid JSON response")
            return None
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def search_item_by_name(name,limit=2):
    """
    Searches for a product by name in the Alegra API.
    
    :param name: The name of the product to search for.
    :param limit: Number of results to fetch.
    :return: JSON response with matching products.
    """
    headers = get_auth_headers()
    params = {
        "limit": limit,
        "name": name  # Search by name 
    }
    response = requests.get(URL, headers=headers, params=params)

    if response.status_code == 200:
        try:
            data = response.json()
            if data:
                data_formated= format_product_results(data)  # Format and display results
                return data_formated
            else:
                print("No products found matching the reference.")
                return None
        except ValueError:
            print("Invalid JSON response.")
            return None
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None
    
def search_item_by_reference(reference,limit=2):
    """
    Searches for a product by reference in the Alegra API.
    
    :param reference: The reference of the product to search for.
    :param limit: Number of results to fetch.
    :return: JSON response with matching products.
    """
    headers = get_auth_headers()
    params = {
        "limit": limit,
        "reference": reference  # Search by reference
    }
    response = requests.get(URL, headers=headers, params=params)

    if response.status_code == 200:
        try:
            data = response.json()
            if data:
                data_formated= format_product_results(data)  # Format and display results
                return data_formated
            else:
                print("No products found matching the reference.")
                return None
        except ValueError:
            print("Invalid JSON response.")
            return None
    else:
        print(f"Error {response.status_code}: {response.text}")
        return None

def format_product_results(products):
    """Formats the search results for better display."""
    formatted_data = []

    for product in products:
        product_info = {
            "ID": product["id"],
            "Referencia": product["reference"],
            "Nombre": product["name"],
            "Categoria": product["itemCategory"]["name"] if "itemCategory" in product else "N/A",
            "Precio": f"{product['price'][0]['price']} {product['price'][0]['currency']['symbol']}" if "price" in product and product["price"] else "N/A",
            "Stock Disponible": product["inventory"]["availableQuantity"] if "inventory" in product else "N/A",
            # "Barcode": product["customFields"][0]["value"] if "customFields" in product and len(product["customFields"]) > 0 else "N/A",
            #"Image URL": product["images"][0]["url"] if "images" in product and len(product["images"]) > 0 else None
        }
        formatted_data.append(product_info)

    df = pd.DataFrame(formatted_data)
    #To show the image of the product
    
    for product in formatted_data:
        image_url = product["images"][0]["url"] if "images" in product and len(product["images"]) > 0 else None
        if image_url:
            print(f"\n🖼️ {product['Nombre']}:")  # 'Nombre' instead of 'Name'
            display(HTML(f'<img src="{image_url}" width="300">'))

    return df

#change rpour les modifier que par l'id pour le reste car quand on récupère despuis alegra on a l'id du produit
def modify_item_by_reference(reference, column, value):
    """
    Modifies a column value of a product by reference in Alegra API.

    :param reference: The reference of the product to search for.
    :param column: The column to modify (e.g., "reference", "description").
    :param value: The new value to set.
    :return: JSON response with the updated product.
    """
    headers = get_auth_headers()

    #Search for the product by name
    search_params = {"limit": 1, "reference": reference} 
    response = requests.get(URL, headers=headers, params=search_params)

    if response.status_code == 200:
        try:
            data = response.json()
            if not data:
                print(f"⚠️ No product found with reference '{reference}'.")
                return None

            product_id = data[0]["id"]  #Extract the ID
            print(f"✅ Found product '{reference}' with ID {product_id}")

            #Modify the product
            update_url = f"{URL}/{product_id}"
            payload = {column: value}  # Column and new value to update
            update_response = requests.put(update_url, json=payload, headers=headers)

            if update_response.status_code == 200:
                print(f"✅ Successfully updated {column} to '{value}' for product ID {product_id}")
                return update_response.json()  # Return updated product info
            else:
                print(f"Error updating product: {update_response.text}")
                return None

        except ValueError:
            print("Invalid JSON response while searching.")
            return None
    else:
        print(f"Error searching for product: {response.text}")
        return None
    
# if __name__ == "__main__":
#     product_name = input("Enter the product name: ")
#     print(f"\n🔍 Searching for products matching '{product_name}'...\n")
#     search_item_by_name(product_name)