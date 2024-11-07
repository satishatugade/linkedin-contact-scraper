import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib.parse import urlparse
import config.database_config as db  # Importing the unchanged database_config file
from sqlalchemy import text
import utils.logging as logger  # Custom logger

def initialize_driver():
    """Initializes the WebDriver for scraping."""
    logger.log_message("Initializing WebDriver", level="info")
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--no-sandbox")
    
    driver = webdriver.Chrome()
    logger.log_message("WebDriver initialized successfully", level="info")
    return driver

def extract_domain(url):
    """Extracts the domain from a given URL."""
    parsed_url = urlparse(url)
    domain = parsed_url.netloc.replace("www.", "")
    logger.log_message(f"Extracted domain: {domain}", level="info")
    return domain if domain and not domain.startswith(('linkedin', 'facebook', 'twitter', 'instagram')) else None

def search_company_workspace(driver, name, max_links=3):
    """Searches for a company's workspace using Google Search."""
    logger.log_message(f"Searching for company workspace for {name}", level="info")
    try:
        driver.get('https://www.google.com')
        search_box = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.NAME, 'q')))
        search_box.clear()
        search_box.send_keys(f'{name} company')
        search_box.send_keys(Keys.RETURN)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.yuRUbf a')))
        results = driver.find_elements(By.CSS_SELECTOR, 'div.yuRUbf a')
        
        domains = []
        for result in results[:max_links]:
            link = result.get_attribute('href')
            domain = extract_domain(link)
            if domain:
                domains.append(domain)
        
        logger.log_message(f"Found domains for {name}: {domains}", level="info")
        return ', '.join(domains) if domains else None
    except Exception as e:
        logger.log_message(f"Error occurred while searching for {name}: {str(e)}", level="error")
        return None

def process_company_data(sddh_id):
    """Processes the company data and updates the database with domain information."""
    logger.log_message("Started processing company data", level="info")

    # Establishing the database connection using psycopg2 from database_config.py
    conn = db.database_connection()
    if conn is None:
        logger.log_message("Database connection failed, stopping the process", level="error")
        return

    # SQL query to fetch contacts without domain
    # fetch_query = "SELECT id, contact_name FROM uq_event_contact_info WHERE domain IS NULL"
    fetch_query = "SELECT id, contact_name FROM uq_event_contact_info WHERE domain IS NULL AND sddh_id = %s"

    try:
        # df = pd.read_sql(fetch_query, conn)
        df = pd.read_sql(fetch_query, conn, params=(sddh_id,))
        logger.log_message(f"Fetched {len(df)} contacts from the database", level="info")
    except Exception as e:
        logger.log_message(f"Failed to fetch contacts from the database: {str(e)}", level="error")
        return

    driver = initialize_driver()
    processed = []
    
    for _, row in df.iterrows():
        record_id = row['id']
        contact_name = row['contact_name']
        logger.log_message(f"Processing contact: {contact_name}", level="info")
        
        # Search for the company domain using Selenium
        company_domains = search_company_workspace(driver, contact_name)
        
        try:
            update_query = "UPDATE uq_event_contact_info SET domain = %s WHERE id = %s"
            with conn.cursor() as cur:
                if company_domains:
                    cur.execute(update_query, (company_domains, record_id))
                    logger.log_message(f"Updated {contact_name} with domains: {company_domains}", level="info")
                    processed.append({contact_name: company_domains})
                else:
                    cur.execute(update_query, ('No company found', record_id))
                    logger.log_message(f"No domains found for {contact_name}", level="info")
        except Exception as db_error:
            logger.log_message(f"Error updating database for {contact_name}: {str(db_error)}", level="error")

        time.sleep(5)  # Sleep to avoid being flagged as a bot

    driver.quit()
    logger.log_message("Driver quit, processing completed", level="info")

    # Close the database connection
    conn.close()
    logger.log_message("Database connection closed", level="info")
    return {"processed": processed}
