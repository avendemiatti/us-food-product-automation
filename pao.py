from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
from urllib.parse import urljoin

# Initialize Selenium WebDriver
driver = webdriver.Chrome()

url = "https://www.paodeacucar.com/busca?terms=estados%20unidos"
driver.get(url)

# Wait until at least one product card is present
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.Card-sc-yvvqkp-0")))

# Allow more time for all products to load
time.sleep(3)

# Get the rendered HTML and quit the driver
html = driver.page_source
driver.quit()

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Find all product cards by their container class
product_cards = soup.find_all('div', class_=lambda c: c and ('Card-sc-yvvqkp-0' in c or 'CardStyled-sc-20azeh-0' in c))

# Prepare CSV file
with open('produtos_estados_unidos.csv', 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Descrição', 'Link'])  # Header row
    
    products_found = 0
    base_url = "https://www.paodeacucar.com"
    
    for card in product_cards:
        # Find the product title container within the card
        title_container = card.find('div', class_=lambda c: c and 'TitleContainer-sc-20azeh-9' in c)
        
        if title_container:
            # Find the product link (with title) within the title container
            link_element = title_container.find('a', href=lambda href: href and '/produto/' in href)
            
            if link_element:
                # Extract description and link
                description = link_element.text.strip()
                href = link_element.get('href')
                full_url = urljoin(base_url, href)
                
                # Write to CSV only if it's a product link
                if '/produto/' in full_url:
                    csv_writer.writerow([description, full_url])
                    products_found += 1
                    
                    # Also print to console
                    print(f"Descrição: {description}")
                    print(f"Link: {full_url}")
                    print("-" * 50)  # Separator for readability

print(f"Done! Found {products_found} products and saved to produtos_estados_unidos.csv")