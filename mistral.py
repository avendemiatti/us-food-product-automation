from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import urllib.parse
import csv

def extract_wine_data(url):
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.get(url)
    time.sleep(3)  # Wait for page to load
    page_source = driver.page_source
    base_url = driver.current_url
    parsed_base = urllib.parse.urlparse(base_url)
    base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"
    
    soup = BeautifulSoup(page_source, 'html.parser')
    wine_data = extract_from_page(soup, base_domain, base_url)
    
    driver.quit()
    return wine_data

def extract_from_page(soup, base_domain, current_url):
    wine_data = []
    # Find product elements by class name hints
    product_elements = soup.find_all(class_=lambda x: x and ('produto' in x.lower() or 'product' in x.lower() or 'showcase' in x.lower()))
    for product in product_elements:
        title_elem = product.find('h2', class_='title-card-showcase')
        link_elem = product.find('a', href=True)
        price_elem = product.find('p', class_='value-wine-card')
        
        if title_elem and link_elem:
            href = link_elem['href']
            full_url = urllib.parse.urljoin(base_domain, href) if not href.startswith('http') else href
            description = title_elem.text.strip()
            if price_elem:
                raw_price = price_elem.get_text(strip=True)
                # Remove "R$" and non-breaking spaces to get only the numeric price
                price = raw_price.replace("R$", "").replace("\xa0", "").strip()
            else:
                price = ""
            wine_data.append({
                'description': description,
                'price': price,
                'url': full_url
            })
    return wine_data

def filter_wine_products(wine_data):
    # Simplified filter: return the data as-is
    return wine_data

def remove_duplicates(wine_data):
    unique = []
    seen_urls = set()
    for item in wine_data:
        if item['url'] not in seen_urls:
            unique.append(item)
            seen_urls.add(item['url'])
    return unique

def save_to_file(wine_data, filename='wine_data.csv'):
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['description', 'price', 'url'])
            writer.writeheader()
            writer.writerows(wine_data)
        print(f"Wine data saved to {filename}")
    except Exception as e:
        print(f"Error saving to file: {e}")

if __name__ == "__main__":
    # Two pages are defined explicitly
    urls = [
        "https://www.mistral.com.br/pais/estados-unidos",
        "https://www.mistral.com.br/pais/estados-unidos?live_sync%5Bquery%5D=estados%20unidos&live_sync%5Bpage%5D=2"
    ]
    
    all_wine_data = []
    for url in urls:
        print(f"Extracting from {url}")
        data = extract_wine_data(url)
        data = filter_wine_products(data)
        all_wine_data.extend(data)
    
    # Remove duplicates based on URL
    unique_wine_data = remove_duplicates(all_wine_data)
    
    print(f"\nFound {len(unique_wine_data)} unique wine products:")
    for i, item in enumerate(unique_wine_data, 1):
        print(f"{i}. Description: {item['description']}")
        print(f"   Price: {item['price']}")
        print(f"   URL: {item['url']}\n")
    
    save_to_file(unique_wine_data)