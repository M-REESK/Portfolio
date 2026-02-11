import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import pandas as pd
import time

def scrape_funda(url, use_selenium=False):
    if use_selenium:
        print("Using Selenium to fetch the page...")
        chrome_options = Options()
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--incognito")

        driver = webdriver.Chrome(options=chrome_options)

        driver.get(url)
        time.sleep(5)

        try:
            agree_button = driver.find_element(By.XPATH, "//button[contains(., 'Agree and close')]")
            agree_button.click()
            print("Accepted cookies!")
            time.sleep(5)
        except Exception as e:
            print(f"Cookie banner not found or already accepted: {e}")

        html = driver.page_source
        driver.quit()
    else:
        print("Using requests to fetch the page...")
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers)
        html = response.text if response.status_code == 200 else None

    return BeautifulSoup(html, "html.parser") if html else None

def get_text(soup, tag, attrs=None, string=None):
    if string:
        element = soup.find(tag, string=string)
    else:
        element = soup.find(tag, attrs)
    return element.get_text(strip=True) if element else "N/A"

def get_attribute(soup, tag, attrs, attr_name):
    element = soup.find(tag, attrs)
    return element.get(attr_name, "N/A") if element else "N/A"

def get_field_value(soup, label):
    element = soup.find("dt", string=lambda t: t and label in t)
    return element.find_next("dd").get_text(strip=True) if element else "N/A"

def clean_price(price):
    return price.replace("kosten koper", "").strip() if price != "N/A" else "N/A"

def create_empty_property_dict(url):
    return {
        "url": url,
        "address": "N/A",
        "square_meters": "N/A",
        "postal_code": "N/A",
        "price": "N/A",
        "price_per_m2": "N/A",
        "monthly_hoa_fee": "N/A",
        "building_year": "N/A",
        "num_rooms": "N/A",
        "status": "N/A",
        "outdoor_space": "N/A",
        "total_volume": "N/A",
        "num_bathrooms": "N/A",
        "energy_label": "N/A",
        "insulation": "N/A",
        "heating": "N/A",
        "hot_water": "N/A",
        "ownership_status": "N/A",
        "charges": "N/A",
        "location": "N/A",
        "balcony_terrace": "N/A"
    }

def parse_property_details(url):
    print(f"Scraping: {url}")
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        return create_empty_property_dict(url)

    soup = BeautifulSoup(response.text, "html.parser")
    
    try:
        # Basic property data
        property_data = {
            "url": url,
            "address": get_text(soup, "span", {"class": "block text-2xl font-bold md:text-3xl lg:text-4xl"}),
            "square_meters": get_text(soup, "span", {"class": "md:font-bold"}),
            "postal_code": get_attribute(soup, "div", {"city": "Amsterdam"}, "postcode"),
            "price": clean_price(get_text(soup, "dd", {"class": "flex border-b border-neutral-20 pb-2 md:py-2"})),
            "price_per_m2": get_text(soup, "dd", {"class": "flex border-b border-neutral-20 pb-2 md:py-2"})
        }

        # Fields to extract
        fields = {
            "monthly_hoa_fee": "VvE bijdrage",
            "building_year": "Bouwjaar",
            "num_rooms": "Aantal kamers",
            "status": "Status",
            "outdoor_space": "Gebouwgebonden buitenruimte",
            "total_volume": "Inhoud",
            "num_bathrooms": "Aantal badkamers",
            "energy_label": "Energielabel",
            "insulation": "Isolatie",
            "heating": "Verwarming",
            "hot_water": "Warm Water",
            "ownership_status": "Eigendomssituatie",
            "charges": "Lasten",
            "location": "Ligging",
            "balcony_terrace": "Balkon/dakterras"
        }

        # Extract all fields
        for key, label in fields.items():
            property_data[key] = get_field_value(soup, label)

        return property_data
    except Exception as e:
        print(f"Error parsing {url}: {e}")
        return create_empty_property_dict(url)

def main():
    base_url = "https://www.funda.nl/en/koop/amsterdam/"
    soup = scrape_funda(base_url, use_selenium=True)
    
    if not soup:
        print("Failed to load the main page.")
        return

    property_links = [f"https://www.funda.nl{prop.get('href')}" 
                     for prop in soup.find_all("a", class_="group") 
                     if prop.get("href")]

    print(f"Found {len(property_links)} properties.")

    results = []
    for link in property_links:
        details = parse_property_details(link)
        results.append(details)
    
    df = pd.DataFrame(results)
    df.to_csv("funda_listings_details.csv", index=False)
    print("Data saved to funda_listings_details.csv")

if __name__ == "__main__":
    main()