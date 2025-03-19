from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import time
import csv
from urllib.parse import urljoin

# Initialize Selenium WebDriver with options
options = Options()
options.add_argument("--start-maximized")  # Maximize window to ensure all elements are visible
driver = webdriver.Chrome(options=options)

# Base URL and output file
base_url = "https://www.karamellstore.com.br"
output_file = "us products karamell.csv"

# Create CSV file and write header
with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Product Name', 'URL'])
    
    # Iterate through all 8 pages
    total_products = 0
    for page_num in range(1, 9):
        # Navigate to the page
        page_url = f"{base_url}/produtos?q=estados+unidos&page={page_num}"
        print(f"Navigating to page {page_num}: {page_url}")
        driver.get(page_url)
        
        # Wait for products to load
        try:
            wait = WebDriverWait(driver, 10)
            wait.until(EC.presence_of_element_located((By.CLASS_NAME, "product-card")))
            # Extra wait to ensure dynamic content is loaded
            time.sleep(2)
        except TimeoutException:
            print(f"Timeout waiting for products on page {page_num}. Moving to next page.")
            continue
        
        # Get page source and parse with BeautifulSoup
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find all product cards
        product_cards = soup.find_all('div', class_='product-card')
        
        print(f"Found {len(product_cards)} products on page {page_num}")
        
        # Extract information from each product card
        for card in product_cards:
            try:
                # Extract product name from data-product-name attribute
                product_name = card.get('data-product-name')
                
                # Try to get URL from data-product-url attribute
                product_url = card.get('data-product-url')
                
                # If data-product-url is not available or incomplete, try alternative methods
                if not product_url:
                    # Try to get from the product-link href
                    link = card.find('a', class_='product-link')
                    if link and link.has_attr('href'):
                        product_url = urljoin(base_url, link['href'])
                elif not product_url.startswith('http'):
                    # If product_url is just a path, join with base_url
                    product_url = urljoin(base_url, product_url)
                
                # Skip if either name or URL is missing
                if not product_name or not product_url:
                    print(f"Skipping product with missing data. Name: {product_name}, URL: {product_url}")
                    continue
                
                # Write to CSV
                writer.writerow([product_name, product_url])
                total_products += 1
                
                # Print for debugging
                print(f"Product: {product_name}")
                print(f"URL: {product_url}")
                print("-" * 50)
                
            except Exception as e:
                print(f"Error processing a product: {e}")
                continue

# Close the driver
driver.quit()

print(f"Scraping completed! Total products found: {total_products}")
print(f"Data saved to {output_file}")