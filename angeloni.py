from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
from bs4 import BeautifulSoup

# Initialize Selenium WebDriver (make sure you have the driver installed, e.g., chromedriver)
driver = webdriver.Chrome()

url = "https://www.angeloni.com.br/super/americano?_q=americano&map=ft"
driver.get(url)

# Wait until at least one product description element is present (adjust the timeout if needed)
wait = WebDriverWait(driver, 10)
wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "span.vtex-product-summary-2-x-brandName")))

# Once loaded, get the page source
html = driver.page_source
driver.quit()

# Parse with BeautifulSoup
soup = BeautifulSoup(html, 'html.parser')
product_spans = soup.select("span[class*='vtex-product-summary-2-x-brandName']")

if product_spans:
    for span in product_spans:
        description = span.get_text(strip=True)
        # Normalize whitespace and convert to lowercase for matching
        normalized = re.sub(r'\s+', ' ', description).lower()
        if (("vinho" in normalized and "americano" in normalized) or 
            ("whisky" in normalized and "americano" in normalized)):
            print(description)
else:
    print("No product descriptions found.")
