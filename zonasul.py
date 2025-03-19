import csv
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup

# ZonaSul URL for American products and base URL
url = "https://www.zonasul.com.br/americanos/americanos?_q=americanos&fuzzy=0&initialMap=ft&initialQuery=americanos&map=ft,pais-de-origem&operator=and"
base_url = "https://www.zonasul.com.br"

# Set up Selenium WebDriver in headless mode
options = Options()
options.add_argument("--headless")
driver = webdriver.Chrome(options=options)

print(f"Loading URL: {url}")
start_time = time.time()
driver.get(url)
time.sleep(3)  # Wait for the page to load

# Loop to click the "Mostrar mais" button until it is no longer available
while True:
    try:
        load_more_button = driver.find_element(By.XPATH, "//div[contains(text(), 'Mostrar mais')]")
        if load_more_button:
            print("Clicking 'Mostrar mais' button to load more products.")
            load_more_button.click()
            time.sleep(2)  # Wait for new products to load
        else:
            break
    except NoSuchElementException:
        print("No 'Mostrar mais' button found. All products loaded.")
        break
    except Exception as e:
        print(f"Exception occurred: {e}. Stopping click loop.")
        break

# Now parse the page content with BeautifulSoup
soup = BeautifulSoup(driver.page_source, "html.parser")

# Find all product containers (anchor tags with the product class)
product_containers = soup.find_all("a", class_="vtex-product-summary-2-x-clearLink")
print(f"Found {len(product_containers)} products on the page.")

products_data = []
for idx, product in enumerate(product_containers, start=1):
    # Extract the product description
    desc_span = product.find("span", class_="vtex-product-summary-2-x-productBrand")
    if not desc_span:
        desc_span = product.find("span", class_="vtex-product-summary-2-x-brandName")
    description = desc_span.get_text(strip=True) if desc_span else "N/A"
    
    # Extract price by concatenating the integer, decimal, and fraction parts
    int_part = product.find("span", class_="zonasul-zonasul-store-1-x-currencyInteger")
    dec_part = product.find("span", class_="zonasul-zonasul-store-1-x-currencyDecimal")
    frac_part = product.find("span", class_="zonasul-zonasul-store-1-x-currencyFraction")
    if int_part and dec_part and frac_part:
        price = int_part.get_text(strip=True) + dec_part.get_text(strip=True) + frac_part.get_text(strip=True)
    else:
        price = "N/A"
    
    # Extract the product URL and prepend the main site URL if needed
    relative_link = product.get("href")
    full_url = base_url + relative_link if relative_link else "N/A"
    
    print(f"Product {idx}: {description} - Price: {price} - URL: {full_url}")
    
    products_data.append({
        "Description": description,
        "Price": price,
        "URL": full_url
    })

driver.quit()
elapsed_time = time.time() - start_time
print(f"\nScraping finished in {elapsed_time:.2f} seconds. Total products: {len(products_data)}")

# Save the scraped data into a CSV file
csv_filename = "zonasul-americanos-products.csv"
with open(csv_filename, mode="w", newline="", encoding="utf-8") as file:
    fieldnames = ["Description", "Price", "URL"]
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for product in products_data:
        writer.writerow(product)

print(f"Data has been saved to '{csv_filename}'")