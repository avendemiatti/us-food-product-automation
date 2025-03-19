from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import urllib.parse
import csv
import re

def extract_wine_data(url, max_pages=5):
    """
    Extract all wine products from the given URL and its pagination.
    
    Args:
        url (str): Base URL to scrape
        max_pages (int): Maximum number of pages to scrape
        
    Returns:
        list: List of dictionaries containing wine URLs and titles
    """
    all_wine_data = []
    current_page = 1
    
    try:
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (no GUI)
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

        # Initialize the Chrome driver
        print("Initializing Chrome driver...")
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        
        # Set a page load timeout
        driver.set_page_load_timeout(30)
        
        # Navigate to the initial URL
        print(f"Navigating to initial page: {url}")
        driver.get(url)
        
        # Process pages until we reach the maximum or no more pagination links
        while current_page <= max_pages:
            print(f"Processing page {current_page}")
            
            # Wait for the page to load
            wait = WebDriverWait(driver, 15)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            # Scroll to load dynamic content
            scroll_to_bottom(driver)

            # Get the page source after JavaScript execution
            page_source = driver.page_source
            
            # Extract base URL for handling relative URLs
            base_url = driver.current_url
            parsed_base = urllib.parse.urlparse(base_url)
            base_domain = f"{parsed_base.scheme}://{parsed_base.netloc}"

            # Parse with BeautifulSoup
            soup = BeautifulSoup(page_source, 'html.parser')

            # Extract wine data from current page
            page_wine_data = extract_from_page(soup, base_domain, base_url)
            
            # Filter for actual wine products
            filtered_wine_data = filter_wine_products(page_wine_data)
            
            print(f"Found {len(filtered_wine_data)} wine products on page {current_page}")
            all_wine_data.extend(filtered_wine_data)
            
            # Check if we need to go to the next page
            if current_page >= max_pages:
                print(f"Reached maximum page limit ({max_pages})")
                break
                
            # Find and click the next page link
            next_page_clicked = click_next_page(driver, current_page)
            
            if not next_page_clicked:
                print(f"No more pages found after page {current_page}")
                break
                
            # Wait for the next page to load after clicking
            time.sleep(3)  # Give some time for the page to start loading
            try:
                # Wait for the URL to change or a specific element to indicate new page load
                WebDriverWait(driver, 10).until(
                    lambda d: f"pg={current_page+1}" in d.current_url or 
                              f"Page {current_page+1}" in d.page_source
                )
            except:
                # If the wait times out, we'll proceed anyway
                print("Warning: Next page may not have loaded completely")
                
            # Increment page counter
            current_page += 1
        
        # Close the driver
        driver.quit()
        
        # Remove duplicates by URL
        seen_urls = set()
        unique_wine_data = []
        for item in all_wine_data:
            if item['url'] not in seen_urls:
                seen_urls.add(item['url'])
                unique_wine_data.append(item)
        
        print(f"Found {len(unique_wine_data)} unique wine products across {current_page-1} pages")
        
        return unique_wine_data
        
    except Exception as e:
        print(f"An error occurred: {e}")
        if 'driver' in locals():
            driver.quit()
        return all_wine_data

def extract_from_page(soup, base_domain, current_url):
    """
    Extract wine data from a single page.
    
    Args:
        soup (BeautifulSoup): Parsed HTML of the page
        base_domain (str): Base domain for resolving relative links
        current_url (str): Current page URL
        
    Returns:
        list: List of dictionaries containing wine URLs and titles
    """
    wine_data = []
    
    # Find all product elements that might contain both title and URL
    product_elements = soup.find_all(class_=lambda x: x and ('produto' in x.lower() or 'product' in x.lower() or 'showcase' in x.lower()))
    
    for product in product_elements:
        # Find title within this product element
        title_elem = product.find('h2', class_='title-card-showcase')
        # Find link within this product element
        link_elem = product.find('a', href=True)
        
        if title_elem and link_elem:
            href = link_elem['href']
            
            # Make sure we have an absolute URL
            if not href.startswith('http'):
                # Handle relative URLs
                if href.startswith('/'):
                    full_url = urllib.parse.urljoin(base_domain, href)
                else:
                    full_url = urllib.parse.urljoin(current_url, href)
            else:
                full_url = href
            
            # Check if "vinho" is in the URL
            if "vinho" in full_url:
                title = title_elem.text.strip()
                wine_data.append({
                    'url': full_url,
                    'title': title
                })
    
    # If the above approach didn't find any matches, try a more general approach
    if not wine_data:
        print("Using alternate extraction method...")
        
        # Find all titles
        titles = soup.find_all('h2', class_='title-card-showcase')
        
        for title_elem in titles:
            title = title_elem.text.strip()
            
            # Look for closest parent with an anchor tag
            parent = title_elem.parent
            max_depth = 5  # Limit how far up we go to find a link
            depth = 0
            
            while parent and depth < max_depth:
                link = parent.find('a', href=True)
                if link:
                    href = link['href']
                    # Make sure we have an absolute URL
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            full_url = urllib.parse.urljoin(base_domain, href)
                        else:
                            full_url = urllib.parse.urljoin(current_url, href)
                    else:
                        full_url = href
                    
                    if "vinho" in full_url:
                        wine_data.append({
                            'url': full_url,
                            'title': title
                        })
                    break
                
                parent = parent.parent
                depth += 1
    
    return wine_data

def click_next_page(driver, current_page):
    """
    Find and click the link to the next page.
    
    Args:
        driver: Selenium WebDriver instance
        current_page (int): Current page number
        
    Returns:
        bool: True if next page was found and clicked, False otherwise
    """
    next_page_num = current_page + 1
    
    # Try to find next page button using different selectors
    selectors = [
        f"//a[contains(@class, 'Pagination-link') and @aria-label='Page {next_page_num}']",
        f"//a[contains(@class, 'Pagination-link') and text()='{next_page_num}']",
        f"//a[contains(@class, 'Pagination') and contains(text(), '{next_page_num}')]",
        f"//a[contains(@class, 'pagination') and contains(text(), '{next_page_num}')]",
        f"//a[contains(@class, 'page') and text()='{next_page_num}']",
        f"//li[contains(@class, 'pagination')]/a[text()='{next_page_num}']",
        "//a[contains(@class, 'Pagination-link') and contains(@aria-label, 'Next')]",
        "//a[contains(@class, 'next')]"
    ]
    
    for selector in selectors:
        try:
            # Try to find the element
            next_page_element = driver.find_element(By.XPATH, selector)
            
            # Try to ensure it's clickable (scrolling to it)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", next_page_element)
            time.sleep(1)  # Give a moment for the scroll to complete
            
            # Click the next page link
            print(f"Found page {next_page_num} link, clicking...")
            next_page_element.click()
            return True
        except Exception as e:
            continue  # Try the next selector

    # If we couldn't find a next page button, log and return False
    print(f"Could not find link to page {next_page_num}")
    return False

def filter_wine_products(wine_data):
    """
    Filter the data to include only actual wine products.
    
    Args:
        wine_data (list): List of dictionaries containing wine URLs and titles
        
    Returns:
        list: Filtered list of wine products
    """
    filtered_data = []
    
    for item in wine_data:
        title = item['title']
        
        # Pattern 1: Look for vintage years (e.g., 2019, 2022)
        has_year = bool(re.search(r'\b20\d{2}\b', title))
        
        # Pattern 2: Look for wine varieties
        wine_varieties = ['cabernet', 'chardonnay', 'merlot', 'pinot', 'sauvignon', 
                          'zinfandel', 'syrah', 'malbec', 'blanc', 'noir', 'red',
                          'white', 'rosé', 'rose', 'shiraz', 'grenache']
        
        has_variety = any(variety.lower() in title.lower() for variety in wine_varieties)
        
        # Pattern 3: Look for wine producers with "vineyards" or "winery" in name
        wine_producers = ['vineyard', 'winery', 'cellars', 'estate', 'chateau', 'domaine', 'bodega']
        has_producer = any(producer.lower() in title.lower() for producer in wine_producers)
        
        # Pattern 4: Specific words that strongly indicate it's a wine
        wine_indicators = ['cuvée', 'cuvee', 'reserve', 'grand cru', 'premier cru', 'brut', 
                           'vintage', 'tinto', 'vinho', 'wine']
        has_indicator = any(indicator.lower() in title.lower() for indicator in wine_indicators)
        
        # Pattern 5: Look for parentheses with winery names (common in wine titles)
        has_parentheses = bool(re.search(r'\([^)]+\)', title))
        
        # Consider it a wine if it matches at least one of these patterns
        if has_year or has_variety or has_producer or has_indicator or has_parentheses:
            filtered_data.append(item)
    
    return filtered_data

def scroll_to_bottom(driver):
    """
    Scroll down the page to load dynamic content.
    
    Args:
        driver: Selenium WebDriver instance
    """
    # Initial scroll height
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Maximum number of scrolls to prevent infinite loops
    max_scrolls = 20
    scroll_count = 0
    
    while scroll_count < max_scrolls:
        # Scroll down in smaller increments
        driver.execute_script("window.scrollBy(0, 500);")
        time.sleep(1)
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # Try one more scroll to be sure
            driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(2)
            newest_height = driver.execute_script("return document.body.scrollHeight")
            if newest_height == new_height:
                break
        last_height = new_height
        scroll_count += 1

def save_to_file(wine_data, filename='wine_data.csv'):
    """
    Save the extracted wine data to a CSV file.
    
    Args:
        wine_data (list): List of dictionaries containing wine URLs and titles
        filename (str): Name of the file to save to
    """
    try:
        with open(filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['title', 'url'])
            writer.writeheader()
            for item in wine_data:
                writer.writerow(item)
        print(f"Wine data saved to {filename}")
    except Exception as e:
        print(f"Error saving to file: {e}")

def print_debug_info(driver):
    """
    Print debug information about the current page
    """
    print(f"Current URL: {driver.current_url}")
    
    # Try to find pagination elements and print information about them
    try:
        pagination_elements = driver.find_elements(By.XPATH, "//a[contains(@class, 'Pagination-link')]")
        print(f"Found {len(pagination_elements)} pagination elements:")
        for elem in pagination_elements:
            try:
                print(f"  Text: '{elem.text}', Aria-Label: '{elem.get_attribute('aria-label')}', Href: '{elem.get_attribute('href')}'")
            except:
                print("  Could not get complete information for this element")
    except:
        print("Could not find pagination elements")

if __name__ == "__main__":
    target_url = "https://www.mistral.com.br/pais/estados-unidos"
    
    print(f"Starting extraction from {target_url}")
    wine_data = extract_wine_data(target_url, max_pages=5)  # Process up to 5 pages
    
    # Print the results
    if wine_data:
        print(f"\nFound {len(wine_data)} wine products:")
        for i, item in enumerate(wine_data, 1):
            print(f"{i}. Title: {item['title']}")
            print(f"   URL: {item['url']}")
            print("-" * 50)
        
        # Save results to CSV file
        save_to_file(wine_data)
    else:
        print("No wine products were found.")