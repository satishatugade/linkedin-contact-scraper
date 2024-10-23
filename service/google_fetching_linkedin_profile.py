from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import time
from webdriver_manager.chrome import ChromeDriverManager
import utils.logging as logger

def initialize_driver():
    chrome_options = Options()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    driver = webdriver.Chrome()
    return driver

def get_linkedin_urls(driver, contact_name, occupation):
    logger.log_message(f"Searching LinkedIn profiles for contact: {contact_name}, occupation: {occupation}", level='info')
    wait = WebDriverWait(driver, 15)
    try:
        driver.get("https://www.google.com")
        search_box = wait.until(EC.visibility_of_element_located((By.NAME, "q")))

        occupation_snippet = ' '.join(occupation.split()[:5]) if occupation else "" 
        search_query = f'{contact_name} {occupation_snippet} LinkedIn profile'
        logger.log_message(f"Search box query{search_query}", level='info')
        search_box.send_keys(search_query)
        search_box.send_keys(Keys.RETURN)

        linkedin_urls = set()
        linkedin_results = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, 'linkedin.com/in/')]")))
        
        for result in linkedin_results:
            linkedin_url = result.get_attribute('href')
            linkedin_urls.add(linkedin_url)
            if len(linkedin_urls) >= 3:
                break

        if len(linkedin_urls) < 3:
            logger.log_message("Less than 3 LinkedIn profiles found, refining search",level='info')
            linkedin_urls.clear()  
            search_box = wait.until(EC.visibility_of_element_located((By.NAME, "q")))
            search_box.clear()
            search_box.send_keys(f'{contact_name} LinkedIn')
            search_box.send_keys(Keys.RETURN)
            linkedin_result = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'linkedin.com')]")))
            linkedin_url = linkedin_result.get_attribute('href')
            linkedin_urls.add(linkedin_url)
        logger.log_message(f"Found LinkedIn URLs: {linkedin_urls}",level='info')
        return ', '.join(list(linkedin_urls)[:3]) if linkedin_urls else "No LinkedIn profile found"
    
    except (TimeoutException, NoSuchElementException, StaleElementReferenceException) as e:
        logger.log_message(f"Error during LinkedIn search: {e}",level='error')
        return f"Error: {e}"
    
    except Exception as e:
        logger.log_message(f" unexpected error {e}",level='error')
        return f"Unexpected error: {e}"

def process_contacts(contacts, cursor, db_connection):
    driver = initialize_driver()

    for contact in contacts:
        contact_id, contact_name, occupation = contact
        logger.log_message(f"Processing contact: {contact_name}, ID: {contact_id}",level='info')

        linkedin_urls = get_linkedin_urls(driver, contact_name, occupation)

        try:
            update_query = "UPDATE uq_event_contact_info SET profile_url = %s WHERE id = %s"
            cursor.execute(update_query, (linkedin_urls, contact_id))
            db_connection.commit()
            logger.log_message(f"Successfully updated database for {contact_name}: {linkedin_urls}",level="info")

            print(f"Processed {contact_name}: {linkedin_urls}")

        except Exception as db_error:
            print(f"Error updating database for {contact_name}: {db_error}")
            logger.log_message(f"Error updating database for {contact_name}: {db_error}",level='error')

        time.sleep(5)  

    driver.quit()
