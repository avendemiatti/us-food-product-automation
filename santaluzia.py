import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# Set up Selenium WebDriver in headless mode
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

# Base URLs
base_site_url = "https://www.santaluzia.com.br"
base_page_url = "https://www.santaluzia.com.br/mercearia/estados-unidos?initialMap=c&initialQuery=mercearia&map=category-1,origem"

products_data = []
page = 1

while True:
    # Construct URL for page 1 differently from subsequent pages
    if page == 1:
        url = base_page_url
    else:
        url = f"https://www.santaluzia.com.br/mercearia/estados-unidos?map=category-1,origem&initialMap=c&initialQuery=mercearia&page={page}"
    
    print(f"Loading page {page}: {url}")
    driver.get(url)
    # Wait for page to load; adjust if needed
    time.sleep(3)
    
    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Check if there's a "no products found" message (using a known class from the error message)
    not_found = soup.find("div", class_="vtex-search-result-3-x-searchNotFound")
    if not_found:
        print(f"No products found on page {page}. Ending extraction.")
        break

    # Find all products on the current page
    products = soup.find_all("div", class_="vtex-search-result-3-x-galleryItem")
    if not products:
        print(f"No products found on page {page}. Ending extraction.")
        break

    print(f"Extracting page {page}: found {len(products)} products")
    
    # Process each product on the page
    for product in products:
        # Extract description from the specified span element
        desc_span = product.find("span", class_="vtex-product-summary-2-x-productBrand")
        description = desc_span.get_text(strip=True) if desc_span else "N/A"
        
        # Extract price parts and combine them
        int_span = product.find("span", class_="vtex-product-price-1-x-currencyInteger")
        dec_span = product.find("span", class_="vtex-product-price-1-x-currencyDecimal")
        frac_span = product.find("span", class_="vtex-product-price-1-x-currencyFraction")
        if int_span and dec_span and frac_span:
            price = int_span.get_text(strip=True) + dec_span.get_text(strip=True) + frac_span.get_text(strip=True)
        else:
            price = "N/A"
        
        # Extract product link and add the main URL if relative
        a_tag = product.find("a", href=True)
        if a_tag:
            relative_link = a_tag["href"]
            product_url = base_site_url + relative_link
        else:
            product_url = "N/A"
        
        products_data.append({
            "Description": description,
            "Price": price,
            "URL": product_url
        })
    
    page += 1

driver.quit()

# Save the scraped data into a CSV file
csv_filename = "santaluzia U.S. products.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    fieldnames = ["Description", "Price", "URL"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for product in products_data:
        writer.writerow(product)

print(f"Finished. {len(products_data)} products found in total.")
print(f"Data has been saved to '{csv_filename}'")