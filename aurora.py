from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException
from bs4 import BeautifulSoup
import time
import csv
from urllib.parse import urljoin

# Initialize Selenium WebDriver with options
options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")  # Maximize window to ensure button is visible
driver = webdriver.Chrome(options=options)

url = "https://www.aurora.com.br/estados%20unidos?_q=estados%20unidos&map=ft"
driver.get(url)

# Wait until initial product elements are loaded
wait = WebDriverWait(driver, 15)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".vtex-product-summary-2-x-brandName")))

# Function to check if "Mostrar mais" button exists
def check_load_more_button():
    try:
        # Find the "Mostrar mais" button
        buttons = driver.find_elements(By.XPATH, "//button[.//div[contains(text(), 'Mostrar mais')]]")
        return len(buttons) > 0
    except NoSuchElementException:
        return False

# Function to click "Mostrar mais" button
def click_load_more():
    try:
        # Different ways to find the button
        button_selectors = [
            "//button[.//div[contains(text(), 'Mostrar mais')]]",
            "//div[contains(text(), 'Mostrar mais')]",
            "//button[contains(@class, 'vtex-button') and .//div[contains(text(), 'Mostrar mais')]]"
        ]
        
        for selector in button_selectors:
            try:
                buttons = driver.find_elements(By.XPATH, selector)
                if buttons:
                    # Scroll to the button to make it visible
                    driver.execute_script("arguments[0].scrollIntoView(true);", buttons[0])
                    time.sleep(1)  # Wait a moment after scrolling
                    buttons[0].click()
                    return True
            except:
                continue
                
        return False
    except (ElementClickInterceptedException, NoSuchElementException) as e:
        print(f"Error clicking button: {e}")
        return False

# Load all products by clicking "Mostrar mais" until no more products load
max_attempts = 10
attempt = 0
previous_product_count = 0

while attempt < max_attempts:
    # Get current product count
    products = driver.find_elements(By.CSS_SELECTOR, ".vtex-product-summary-2-x-brandName")
    current_product_count = len(products)
    
    print(f"Current product count: {current_product_count}")
    
    # If no more new products are loading, we're done
    if current_product_count == previous_product_count:
        # Check if the button still exists
        if not check_load_more_button():
            print("No more 'Mostrar mais' button found. All products loaded.")
            break
    
    previous_product_count = current_product_count
    
    # Try to click "Mostrar mais" button
    if not click_load_more():
        print("Could not click 'Mostrar mais' button.")
        # Try one more time with a longer wait
        time.sleep(2)
        if not click_load_more():
            print("Still could not click 'Mostrar mais' button after retry.")
            break
    
    # Wait for new products to load
    try:
        time.sleep(3)  # Give it more time to load new content
    except TimeoutException:
        print("Timeout waiting for new products to load.")
        break
    
    attempt += 1

# After loading all products, get the final page source
time.sleep(2)  # One final wait to ensure everything is loaded
html = driver.page_source

# Print total products found before extraction
final_products = driver.find_elements(By.CSS_SELECTOR, ".vtex-product-summary-2-x-brandName")
print(f"Total products found in page: {len(final_products)}")

# Quit the driver
driver.quit()

# Parse the HTML with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')

# Find all product elements - using the specific class for product names
product_names = soup.find_all('span', class_='vtex-product-summary-2-x-productBrand vtex-product-summary-2-x-brandName t-body')

# Prepare CSV file
with open('produtos_aurora.csv', 'w', newline='', encoding='utf-8') as csv_file:
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Descrição', 'Link'])  # Header row
    
    products_found = 0
    base_url = "https://www.aurora.com.br"
    
    for product_name in product_names:
        # Get the product description
        description = product_name.text.strip()
        
        # Find the parent link element that contains the href
        parent_link = product_name.find_parent('a', class_=lambda c: c and 'vtex-store-link-0-x-link' in c)
        
        if parent_link:
            # Get the relative URL
            href = parent_link.get('href')
            # Create the full URL
            full_url = urljoin(base_url, href)
            
            # Write to CSV
            csv_writer.writerow([description, full_url])
            products_found += 1
            
            # Also print to console
            print(f"Descrição: {description}")
            print(f"Link: {full_url}")
            print("-" * 50)  # Separator for readability

print(f"Done! Found and saved {products_found} products to produtos_aurora.csv")

# Verify we got all 23 products
if products_found < 23:
    print(f"WARNING: Only found {products_found} products, but there should be 23 products total.")
    print("Some products may have been missed.")
else:
    print("Successfully extracted all expected products!")