import csv
import time
import urllib.parse as urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup

# List of category URLs to scrape
category_urls = [
    "https://www.santaluzia.com.br/adega/estados-unidos?initialMap=c&initialQuery=adega&map=category-1,origem",
    "https://www.santaluzia.com.br/bebidas/estados-unidos?initialMap=c&initialQuery=bebidas&map=category-1,origem",
    "https://www.santaluzia.com.br/chocolates/estados-unidos?initialMap=c&initialQuery=chocolates&map=category-1,origem",
    "https://www.santaluzia.com.br/frutas-secas/estados-unidos?initialMap=c&initialQuery=frutas-secas&map=category-1,origem",
    "https://www.santaluzia.com.br/matinais/estados-unidos?initialMap=c&initialQuery=matinais&map=category-1,origem"
]

# Set up Selenium WebDriver in headless mode
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

base_site_url = "https://www.santaluzia.com.br"

# This list will hold all scraped product data
products_data = []

start_time = time.time()

# Loop over each category URL
for cat_url in category_urls:
    # Parse the base path and query for building subsequent pages
    parsed = urlparse.urlparse(cat_url)
    params = urlparse.parse_qs(parsed.query)
    # Extract the initialQuery parameter which typically is the category keyword
    query_val = params.get("initialQuery", [""])[0]
    # The base path (without query parameters) is used for building page URLs
    base_path = cat_url.split('?')[0]
    
    print(f"\nProcessing category: '{query_val}'")
    page = 1
    while True:
        # Construct URL: for page 1 use the original URL; otherwise, append the page parameter
        if page == 1:
            current_url = cat_url
        else:
            current_url = f"{base_path}?map=category-1,origem&initialMap=c&initialQuery={query_val}&page={page}"
        
        print(f"  Loading page {page}: {current_url}")
        driver.get(current_url)
        # Wait for the page to load (adjust if necessary)
        time.sleep(3)
        
        soup = BeautifulSoup(driver.page_source, "html.parser")
        
        # Check for a "no products found" message
        not_found = soup.find("div", class_="vtex-search-result-3-x-searchNotFound")
        if not_found:
            print(f"  No products found on page {page} for '{query_val}'. Moving to next category.")
            break
        
        # Find all product blocks
        products = soup.find_all("div", class_="vtex-search-result-3-x-galleryItem")
        if not products:
            print(f"  No products found on page {page} for '{query_val}'. Ending extraction for this category.")
            break
        
        print(f"  Extracting page {page}: found {len(products)} products")
        
        # Process each product
        for product in products:
            # Extract the description
            desc_span = product.find("span", class_="vtex-product-summary-2-x-productBrand")
            description = desc_span.get_text(strip=True) if desc_span else "N/A"
            
            # Extract the price by concatenating integer, decimal, and fraction parts
            int_span = product.find("span", class_="vtex-product-price-1-x-currencyInteger")
            dec_span = product.find("span", class_="vtex-product-price-1-x-currencyDecimal")
            frac_span = product.find("span", class_="vtex-product-price-1-x-currencyFraction")
            if int_span and dec_span and frac_span:
                price = int_span.get_text(strip=True) + dec_span.get_text(strip=True) + frac_span.get_text(strip=True)
            else:
                price = "N/A"
            
            # Extract the product URL and prepend the main site URL if needed
            a_tag = product.find("a", href=True)
            if a_tag:
                relative_link = a_tag["href"]
                product_url = base_site_url + relative_link
            else:
                product_url = "N/A"
            
            products_data.append({
                "Category": query_val,
                "Description": description,
                "Price": price,
                "URL": product_url
            })
        
        page += 1

driver.quit()

elapsed_time = time.time() - start_time
print(f"\nFinished scraping. Total products found: {len(products_data)}")
print(f"Total elapsed time: {elapsed_time:.2f} seconds")

# Save the scraped data into a CSV file
csv_filename = "santaluzia U.S. products.csv"
with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
    fieldnames = ["Category", "Description", "Price", "URL"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for product in products_data:
        writer.writerow(product)

print(f"Data has been saved to '{csv_filename}'")