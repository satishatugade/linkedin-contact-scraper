import utils.logging as logger
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import psycopg2
from selenium.common.exceptions import ElementClickInterceptedException
import datetime
from service.attendee import fetch_all_selectors, get_selector_info
# from config.database_config as config
from config import database_config as DB
from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException, NoSuchElementException


class ContactInfo:
    def __init__(self, sddh_id, company_linkedin_url,eds_id,event_name, contact_name=None, occupation=None, profile_url=None, created_date=None, error_reason=None):
        self.sddh_id = sddh_id
        self.company_linkedin_url = company_linkedin_url
        self.eds_id=eds_id
        self.event_name=event_name
        self.contact_name = contact_name
        self.occupation = occupation
        self.profile_url = profile_url
        self.created_date = created_date
        self.error_reason = error_reason

    def __str__(self):
        return (f"ContactInfo(sddh_id={self.sddh_id}, company_linkedin_url={self.company_linkedin_url},eds_id={self.eds_id},event_name={self.event_name} "
                f"contact_name={self.contact_name}, occupation={self.occupation}, "
                f"profile_url={self.profile_url}, created_date={self.created_date}, "
                f"error_reason={self.error_reason})")    
          
def fetch_linkedin_url_dump_detail_table(sddh_id):
    logger.log_message(f"fetch_linkedin_url_dump_detail_table Event Id :{sddh_id}")
    db_conn = DB.database_connection()
    if not db_conn:
        print("Failed to connect to the database")
        return "failed"
    try:
        cursor = db_conn.cursor()
        query = """SELECT uddd1.sddh_id,uddd1.datapoint_value AS linkedin_link,uds.id as eds_id,LOWER(uddd3.datapoint_value) AS event_name
                   FROM uq_data_dump_details uddd1
                   JOIN 
                        uq_data_dump_details uddd2 ON uddd1.sddh_id = uddd2.sddh_id
                   JOIN 
                        uq_data_dump_details uddd3 ON uddd1.sddh_id = uddd3.sddh_id     
                    LEFT JOIN 
                        uq_data_dump_header uddh ON uddd1.sddh_id = uddh.id
                    LEFT JOIN 
                        uq_project_data_source upds ON uddh.spds_id = upds.id
                    LEFT JOIN 
                        uq_project_result upr ON upds.sp_id = upr.id
                    LEFT JOIN 
                        uq_data_source uds ON upds.eds_id = uds.id
                   WHERE uddd1.datapoint_name = 'LinkedinURL'
                   AND uddd2.datapoint_name = 'LinkedInScrapingState'
                   AND uddd3.datapoint_name = 'EventName'
                   AND uddd2.datapoint_value = 'false'"""
        if sddh_id != "":
            query += " AND uddd1.sddh_id = %s"
            cursor.execute(query, (sddh_id,))
        else:
            cursor.execute(query)
        results = cursor.fetchall()  
        contact_info_list = [ContactInfo(row[0], row[1],row[2],row[3]) for row in results]
        return contact_info_list

    except Exception as e:
        print(f"Failed to execute query: {e}")
        return "failed"
    finally:
        if db_conn:
            cursor.close()
            db_conn.close()  

def update_contact_scraping_status(eds_id, sddh_id, scraping_mode, status, error_reason=None):
    start_time = datetime.datetime.now()
    formatted_start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
    db_conn = DB.database_connection()
    if not db_conn:
        logger.log_message("Failed to connect to the database", level='info')
        return "failed", None
    
    try:
        with db_conn.cursor() as cursor:
            insert_query = """
            INSERT INTO uq_contact_scraping_status (eds_id, sddh_id,start_time, scraping_mode, status, error_reason)
            VALUES (%s,%s, %s, %s, %s, %s)
            RETURNING id
            """
            cursor.execute(insert_query, (eds_id, sddh_id,formatted_start_time, scraping_mode, status, error_reason))
            new_id = cursor.fetchone()[0]  # Retrieve the generated ID
            db_conn.commit()  # Commit the transaction
            logger.log_message("Data inserted successfully", level='info')
            return "success", new_id
    
    except psycopg2.Error as e:
        db_conn.rollback()  # Rollback in case of error
        logger.log_message(f"Error saving data to PostgreSQL: {e}", level='info')
        return "failed", None
    
    finally:
        if db_conn:
            db_conn.close()

def update_contact_scraping_status_by_id(table_id, sddh_id, new_status, new_error_reason=None):
    end_time = datetime.datetime.now()
    formatted_end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")
    db_conn = DB.database_connection()
    if not db_conn:
        logger.log_message("Failed to connect to the database", level='info')
        return "failed"
    
    try:
        with db_conn.cursor() as cursor:
            update_query = """ UPDATE uq_contact_scraping_status SET status = %s,end_time =%s,error_reason = %s WHERE id = %s AND sddh_id = %s"""
            cursor.execute(update_query, (new_status,formatted_end_time, new_error_reason, table_id, sddh_id))
            db_conn.commit() 
            logger.log_message("Status updated successfully", level='info')
            return "success"
    
    except psycopg2.Error as e:
        db_conn.rollback()
        logger.log_message(f"Error updating data in PostgreSQL: {e}", level='info')
        return "failed"
    
    finally:
        if db_conn:
            db_conn.close()


def save_attendee_data(attendee):
    """Save scraped attendee data to the database."""
    db_conn = DB.database_connection()
    if not db_conn:
        logger.log_message(f"Failed to connect to the database",level='info')
        return "failed"
    
    try:
        with db_conn.cursor() as cursor:
            insert_query = """
            INSERT INTO uq_event_contact_info (sddh_id, contact_name, occupation, location, profile_url, linkedin_link, company_linkedin_url, source, error_reason,profile_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s,%s)
            """
            cursor.execute(insert_query, (
                attendee['sddh_id'],
                attendee['name'],
                attendee['occupation'],
                attendee['location'],
                attendee['profile_url'],
                attendee['linkedin_link'], 
                attendee['company_linkedin_url'], 
                attendee['source'],        
                attendee['error_reason'],
                attendee['profile_image']  
            ))

            update_scraping_state_query = """
                UPDATE uq_data_dump_details
                SET datapoint_value = 'true'
                WHERE sddh_id = %s AND datapoint_name = 'LinkedInScrapingState'
            """
            cursor.execute(update_scraping_state_query, (attendee['sddh_id'],))
        
        db_conn.commit()
        logger.log_message(f"Attendee data saved successfully for sddh_id: {attendee['sddh_id']}",level='info')
        return "success"
    except psycopg2.Error as e:
        logger.log_message(f"Error saving data to PostgreSQL: {e}",level='info')
        return "failed"
    finally:
        if db_conn:
            db_conn.close()

def set_linkedin_cookies(driver, session_id, li_at_value):
    """Set LinkedIn cookies (JSESSIONID and li_at) to simulate logged-in session."""
    driver.get("https://www.linkedin.com")
    driver.add_cookie({'name': 'JSESSIONID', 'value': session_id, 'domain': '.linkedin.com'})
    driver.add_cookie({'name': 'li_at', 'value': li_at_value, 'domain': '.linkedin.com'})
    driver.refresh()
    time.sleep(10)  

def is_login_successful(driver):
    """Check if login is successful by waiting for 10 seconds and verifying the current URL."""
    time.sleep(15)  
    if "feed" in driver.current_url:
        logger.log_message(f"Login successful!",level='info')
        return True
    else:
        logger.log_message(f"Login unsuccessful. Current URL: {driver.current_url}",level='error')
        return False
    

def handle_event_registration(driver, wait, selectors):
    try:
        # Locate the main button (Register or Attend)
        try:
            main_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selectors['action_button']['selector_value'])))
            button_text = main_button.text.strip().lower()
            logger.log_message(f"Detected button text: {button_text}", level="info")
        except (TimeoutException, NoSuchElementException) as e:
            logger.log_message(f"Main button not found or not clickable: {str(e)}", level="error")
            return "failed"

        # Handle "Register" button
        if "register" in button_text:
            try:
                logger.log_message("Clicking the 'Register' button", level="info")
                main_button.click()
                time.sleep(5)  # Wait for the registration modal to appear

                # Locate and click the checkbox
                checkbox_selector = selectors.get("presence_checkbox")
                if checkbox_selector:
                    try:
                        logger.log_message("Attempting to click the associated <label> element", level="info")
                        label = driver.find_element(By.CSS_SELECTOR, f"label[for='{checkbox_selector['selector_value'].split('#')[1]}']")
                        label.click()
                        logger.log_message("Successfully clicked the <label> element", level="info")
                    except Exception as e:
                        logger.log_message(f"Label click failed: {str(e)}. Falling back to JavaScript for checkbox click.", level="warning")
                        checkbox = driver.find_element(getattr(By, checkbox_selector['selector_type'].upper()), checkbox_selector['selector_value'])
                        driver.execute_script("arguments[0].click();", checkbox)
                        logger.log_message("Successfully clicked the checkbox using JavaScript", level="info")

                # Click the submit button
                submit_selector = selectors.get("submit_button")
                if submit_selector:
                    try:
                        logger.log_message("Clicking the 'Submit' button", level="info")
                        submit_button = wait.until(EC.element_to_be_clickable((getattr(By, submit_selector['selector_type'].upper()), submit_selector['selector_value'])))
                        driver.execute_script("arguments[0].click();", submit_button)
                        logger.log_message("Successfully clicked the 'Submit' button", level="info")
                        time.sleep(5)  # Wait for the registration process to complete
                    except Exception as e:
                        logger.log_message(f"Failed to click 'Submit' button: {str(e)}", level="error")
                        return "failed"
            except (ElementClickInterceptedException, Exception) as e:
                logger.log_message(f"Failed to click 'Register' button: {str(e)}", level="error")
                return "failed"

        # Handle "Attend" button
        elif "attend" in button_text:
            try:
                logger.log_message("Clicking the 'Attend' button", level="info")
                main_button.click()
                time.sleep(5)  # Wait for the attendance process to complete
                logger.log_message("Successfully clicked the 'Attend' button", level="info")
            except (ElementClickInterceptedException, Exception) as e:
                logger.log_message(f"Failed to click 'Attend' button: {str(e)}", level="error")
                return "failed"

        # Check for attendees link after registration or attendance
        attendee_selector = selectors.get("attendees_link")
        if attendee_selector:
            try:
                logger.log_message("Looking for 'Attendees' link", level="info")
                attendee_link = wait.until(EC.element_to_be_clickable((getattr(By, attendee_selector['selector_type'].upper()), attendee_selector['selector_value'])))
                attendee_link.click()
                logger.log_message("Successfully clicked the 'Attendees' link", level="info")
                return "success"
            except Exception as e:
                logger.log_message(f"Failed to find or click 'Attendees' link: {str(e)}", level="error")
                return "failed"
        else:
            logger.log_message("Attendees link selector not found in the selectors dictionary.", level="error")
            return "failed"

    except Exception as e:
        logger.log_message(f"Error during event registration process: {str(e)}", level="error")
        return "failed"
def scroll_and_click_element(driver, wait, element_name, selectors):
   
    try:
        element_selector_info = get_selector_info(element_name, selectors)
        if not element_selector_info:
            logger.log_message(f"{element_name} selector not found in the database.", level="error")
            return False

        element_selector_type, element_selector_value = element_selector_info
        element = wait.until(EC.presence_of_element_located((getattr(By, element_selector_type), element_selector_value)))
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(2)  # Allow the page to adjust
        element.click()
        logger.log_message(f"{element_name} clicked successfully.", level="info")
        return True
    except Exception as e:
        logger.log_message(f"Error while scrolling and clicking {element_name}: {str(e)}", level="error")
        return False

def click_submit_button(wait, selectors):

    try:
        submit_selector_info = get_selector_info("submit_button", selectors)
        if not submit_selector_info:
            logger.log_message("Submit button selector not found in the database.", level="error")
            return False

        submit_selector_type, submit_selector_value = submit_selector_info
        submit_button = wait.until(EC.element_to_be_clickable((getattr(By, submit_selector_type), submit_selector_value)))
        submit_button.click()
        logger.log_message("Submit button clicked successfully.", level="info")
        return True
    except Exception as e:
        logger.log_message(f"Error while clicking the submit button: {str(e)}", level="error")
        return False



def check_button_text(driver, wait, selectors):
    """Check the button text to determine whether it is a Register or Attend button."""
    try:
        # Log selectors dictionary for debugging
        logger.log_message(f"Selectors: {selectors}", level="info")

        # Fetch the selector information for the action button
        button_selector_info = selectors.get("action_button")
        if not button_selector_info:
            logger.log_message("Action button selector not found in selectors.", level="error")
            return None

        selector_type = button_selector_info.get("selector_type")
        selector_value = button_selector_info.get("selector_value")

        # Log fetched selector information
        logger.log_message(f"Selector Type: {selector_type}, Selector Value: {selector_value}", level="info")

        if not selector_type or not selector_value:
            logger.log_message("Invalid action button selector in selectors.", level="error")
            return None

        # Locate the button element
        button = wait.until(EC.presence_of_element_located((getattr(By, selector_type.upper()), selector_value)))

        # Get button text
        button_text = button.text.strip()

        # If button text is empty, use JavaScript as a fallback
        if not button_text:
            button_text = driver.execute_script("return arguments[0].textContent.trim();", button)
            if not button_text:
                raise Exception("Action button text is empty.")

        logger.log_message(f"Detected button text: {button_text}", level="info")
        return button_text

    except Exception as e:
        logger.log_message(f"Error checking button text: {str(e)}", level="error")
        return None

def process_event_page(company_linkedin_url, scraping_status_id, sddh_id, event_name, scraping_mode, session_id, li_at_value):
    """Process LinkedIn event page based on scraping mode."""
    logger.log_message(f"inside process_event_page", level='info')
    driver = webdriver.Chrome()
    driver.maximize_window()
    wait = WebDriverWait(driver, 30)
    linkedin_link = None  
    error_reason = None 

    try:
        # Step 1: Login to LinkedIn
        driver.get("https://www.linkedin.com/")
        driver.add_cookie({'name': 'JSESSIONID', 'value': session_id})
        driver.add_cookie({'name': 'li_at', 'value': li_at_value})
        driver.refresh()
        time.sleep(10)

        # Step 2: Check if login is successful
        if not is_login_successful(driver):
            error_reason = "Login failed."
            logger.log_message(f"Login failed. Exiting the process.", level='error')
            update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "failed", error_reason)
            return

        # Step 3: Visit the company LinkedIn URL
        driver.get(company_linkedin_url.strip())
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5)
        logger.log_message(f"Visiting company page: {company_linkedin_url}", level='info')

        selectors = fetch_all_selectors()

        # Step 4: Handle "Register" or "Attend" buttons
        button_text = check_button_text(driver, wait, selectors)

        if button_text == "Register":
            logger.log_message("Register button found. Initiating registration process.", level="info")
            register_status = handle_event_registration(driver, wait, selectors)
            if register_status == "failed":
                error_reason = "Event registration failed."
                logger.log_message(error_reason, level="error")
                update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "failed", error_reason)
                return
            else:
                handle_pagination(driver, wait, scraping_status_id, sddh_id, event_name, scraping_mode, linkedin_link, company_linkedin_url, error_reason, selectors)
                update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "success", error_reason)
 

        elif button_text == "Attend":
            logger.log_message("Attend button found. Clicking Attend button.", level="info")
            if not click_attend_button(wait, selectors):
                error_reason = "Failed to click Attend button."
                logger.log_message(error_reason, level="error")
                update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "failed", error_reason)
                return

        # Step 5: Handle attendee list
        if click_attendees_link(wait, selectors):
            linkedin_link = driver.current_url
            logger.log_message(f"Attendees link found. LinkedIn URL set to: {linkedin_link}", level='info')
            handle_pagination(driver, wait, scraping_status_id, sddh_id, event_name, scraping_mode, linkedin_link, company_linkedin_url, error_reason, selectors)
            update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "success", error_reason)
        else:
            logger.log_message(f"Attendees link not found. Checking for 'Show all events' button.", level='info')

            # Step 6: Check for "Show All Events" button
            if click_show_all_events(driver, wait):
                event_links = get_upcoming_event_links(wait)

                if event_links:
                    logger.log_message(f"Found {len(event_links)} upcoming events.", level='info')

                    # Step 7: Process upcoming events if found
                    for event_link in event_links:
                        linkedin_link = event_link
                        logger.log_message(f"Processing upcoming event link: {event_link}", level='info')
                        process_event_page(event_link, scraping_status_id, sddh_id, event_name, scraping_mode, session_id, li_at_value)
                else:
                    error_reason = "No upcoming events available"
                    logger.log_message(f"No upcoming events available for URL: {company_linkedin_url}", level='info')
                    update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "failed", error_reason)

            else:
                error_reason = "Show All Events button not found."
                logger.log_message(f"Show All Events button not found for URL: {company_linkedin_url}", level='error')
                update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "failed", error_reason)

    except Exception as e:
        logger.log_message(f"An error occurred while visiting linkedin link: {str(e)}", level='error')
        error_reason = str(e)
        update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "failed", error_reason)
    finally:
        driver.quit()

def click_attend_button(wait,selectors):
    """Attempt to click the 'Attend' button."""
    logger.log_message(f"Attempting to click the 'Attend' button",level='info')
    try:
        attend_button = "attend_button"
        selector_info = get_selector_info(attend_button, selectors)

        if not selector_info:
            logger.log_message(f"Failed to get selector information for {attend_button}.", level='error')
            return False  

        selector_type, selector_value = selector_info
        # attend_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-button.artdeco-button--2.artdeco-button--primary.ember-view span.artdeco-button__text")))
        attend_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector_value)))
        attend_button.click()
        time.sleep(5)
        logger.log_message(f"Attend button clicked successfully",level='info')
        return True
    except Exception as e:
        error_reason = "Attend button not found."
        logger.log_message(f"{error_reason}",level='info')
        return False

def click_attendees_link(wait,selectors):
    """Attempt to click the 'Attendees' link."""
    logger.log_message(f"Attempting to click the 'Attendees' link",level='info')
    try:
        attendees_link = "attendees_link"
        selector_info = get_selector_info(attendees_link, selectors)

        if not selector_info:
            logger.log_message(f"Failed to get selector information for {attendees_link}.", level='error')
            return False  

        selector_type, selector_value = selector_info
        # attendees_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.link-without-visited-state.full-width")))
        attendees_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector_value)))
        attendees_link.click()
        time.sleep(5)
        logger.log_message(f"Attendees link clicked successfully",level='info')
        return True
    except Exception as e:
        logger.log_message(f"Attendees link not found.",level='error')
        return False

def click_show_all_events(driver, wait):
    logger.log_message(f"Attempting to click the 'Show all events' button", level='info')
    try:
        show_all_events_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Show all events']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", show_all_events_button)
        time.sleep(3)
        try:
            show_all_events_button.click()
        except ElementClickInterceptedException:
            logger.log_message(f"Element intercepted, retrying click using JavaScript", level='info')
            driver.execute_script("arguments[0].click();", show_all_events_button)  # Retry click with JS
        time.sleep(5)
        logger.log_message(f"Show all events button clicked successfully", level='info')
        return True
    except Exception as e:
        logger.log_message(f"Failed to click 'Show all events' button: {e}", level='error')
        return False
    
def get_upcoming_event_links(wait):
    """Fetch upcoming event links."""
    logger.log_message(f"Fetching upcoming event links",level='info')
    try:
        upcoming_events_section = wait.until(EC.presence_of_element_located((By.XPATH, "//h4[text()='Upcoming events']/following-sibling::ul")))
        event_links = upcoming_events_section.find_elements(By.CSS_SELECTOR, "a.events-components-shared-event-card")
        links = [event.get_attribute('href') for event in event_links]
        logger.log_message(f"Found {len(links)} upcoming event links",level='info')
        return links
    except Exception as e:
        logger.log_message(f"Error fetching upcoming event links:",level='error')
        return []

def click_next_button(driver, wait,selectors):
    """Attempt to click the 'Next' button."""
    logger.log_message(f"Attempting to click the 'Next' button", level='info')
    try:
        next_button_element = "next_button"
        selector_info = get_selector_info(next_button_element, selectors)

        if not selector_info:
            logger.log_message(f"Failed to get selector information for {next_button_element}.", level='error')
            return False  

        selector_type, selector_value = selector_info
        
        # next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Next']")))
        next_button = wait.until(EC.element_to_be_clickable((By.XPATH,selector_value)))
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button) 
        time.sleep(2)  
        try:
            next_button.click()
        except ElementClickInterceptedException:
            logger.log_message(f"Element intercepted, retrying click using JavaScript", level='info')
            driver.execute_script("arguments[0].click();", next_button)  # Retry click with JS

        time.sleep(5)  # Wait after click to load new page
        logger.log_message(f"'Next' button clicked successfully", level='info')
        return True

    except Exception as e:
        logger.log_message(f"Failed to click 'Next' button: {e}", level='error')
        return False

def take_screenshot_of_elements(driver, sddh_id, page_count, folder_path, screenshot_type, elements):
    """
    Takes a screenshot of the visible part of the screen where the elements are located.
    """ 
    driver.execute_script("arguments[0].scrollIntoView(true);", elements[0])
    time.sleep(9)  
    take_screenshot(driver, sddh_id, page_count, folder_path, screenshot_type)
    
def handle_pagination(driver, wait,scraping_status_id, sddh_id,event_name, scraping_mode, linkedin_link, company_linkedin_url, error_reason,selectors):
    """Handle pagination for OCR or Selenium mode."""
    logger.log_message(f"Handling pagination with {scraping_mode} mode.", level='info')
    # page_count = 1
    if scraping_mode == 'ocr':
        page_count = 1
        folder_name = f"{sddh_id}"
        folder_path = os.path.join(os.getcwd(), "screenshots", folder_name)
        os.makedirs(folder_path, exist_ok=True)
        # OCR Mode: Take screenshots of each page.
        while True:
            try:
                reusable_search_result_list = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "reusable-search__entity-result-list"))
                )

                # Get the first 5 elements from the search result list
                list_items = driver.find_elements(By.CSS_SELECTOR, "li.reusable-search__result-container")

                if len(list_items) < 5:
                    logger.log_message("Less than 5 items found. Adjusting logic.", level='info')

                logger.log_message("Taking screenshot of the first 5 elements before scroll.", level='info')
                take_screenshot_of_elements(driver, sddh_id, page_count, folder_path, "before_scroll", list_items[:5])
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                logger.log_message("Taking screenshot of the next 5 elements after scroll.", level='info')
                take_screenshot_of_elements(driver, sddh_id, page_count, folder_path, "after_scroll", list_items[5:10])

                # Check if there is a "next" button to go to the next page
                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-pagination__button--next")))
                    next_button.click()
                    time.sleep(6)
                    page_count += 1
                except Exception as e:
                    logger.log_message(f"No more pages or error clicking next button: {str(e)}. Pagination ended.", level='info')
                    error_reason = f"Pagination ended or error: {str(e)}"
                    attendee = {
                        "sddh_id": sddh_id,
                        "linkedin_link": linkedin_link,
                        "company_linkedin_url": company_linkedin_url,
                        "source": scraping_mode,
                        "error_reason": error_reason
                    }
                    save_status=save_attendee_data(attendee)
                    if save_status =="success":
                        update_contact_scraping_status_by_id(scraping_status_id,sddh_id,"success",error_reason)  
                    break

            except Exception as e:
                logger.log_message(f"Error during OCR pagination: {str(e)}", level='error')
                error_reason = f"Error during OCR pagination: {str(e)}"
                attendee = {
                    "sddh_id": sddh_id,
                    "linkedin_link": linkedin_link,
                    "company_linkedin_url": company_linkedin_url,
                    "source": scraping_mode,
                    "error_reason": error_reason
                }
                save_attendee_data(attendee)
                break

    elif scraping_mode == 'selenium':
        next_page_count=0
        while True:
            try:
                logger.log_message(f"Inside selenium mode scraping",level='info')
                process_attendee_elements(selectors,wait,sddh_id, linkedin_link, company_linkedin_url, scraping_mode, error_reason)
                next_page_count += 0
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                try:
                    # next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-pagination__button--next")))
                    # next_button.click()
                    # logger.log_message(f"next button clicked page_count {next_page_count}",level='info')
                    # time.sleep(6)
                    if not click_next_page(wait, next_page_count,selectors):
                        logger.log_message(f"next_page_count : {next_page_count}",level='info')
                        error_reason = f"No more pages available after {next_page_count} pages."
                        logger.log_message(error_reason, level="info")
                        update_contact_scraping_status_by_id(scraping_status_id, sddh_id, "success", error_reason)
                        break
                except Exception as e:
                    error_reason = f"No more pages or error clicking next button: {str(e)}"
                    update_contact_scraping_status_by_id(scraping_status_id,sddh_id,"success",error_reason)
                    logger.log_message(error_reason, level='error')
                    break

            except Exception as e:
                error_reason = f"Error scraping attendees: {str(e)}"
                update_contact_scraping_status_by_id(scraping_status_id,sddh_id,"success",error_reason)
                logger.log_message(error_reason, level='error')
                break

def take_screenshot(driver, sddh_id, page_count, folder_path, prefix):
    """Take a screenshot for OCR-based processing with correct naming."""
    screenshot_path = os.path.join(folder_path, f"{sddh_id}_{prefix}_page_{page_count}.png")
    driver.save_screenshot(screenshot_path)
    logger.log_message(f"Screenshot saved: {screenshot_path}",level='info')

def click_next_page(wait, next_page_count,selectors):
    try:
        next_page = "next_page"
        selector_info = get_selector_info(next_page, selectors)

        if not selector_info:
            logger.log_message(f"Failed to get selector information for {next_page}.", level='error')
            return False  

        selector_type, selector_value = selector_info
        next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector_value)))
        # next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-pagination__button--next")))
        next_button.click()
        logger.log_message(f"Next button clicked. Page count: {next_page_count}", level="info")
        time.sleep(6)  # Allow time for the next page to load
        return True
    except Exception as e:
        logger.log_message(f"Failed to click the next button on page {next_page_count}: {str(e)}", level="error")
        return False

def process_attendee_elements(selectors,wait,sddh_id, linkedin_link, company_linkedin_url, scraping_mode, error_reason):
    try:
        # List of attendees on linkedin page
        try:
            search_list = "reusable_search_result_list"
            selector_info = get_selector_info(search_list, selectors)

            if not selector_info:
                logger.log_message(f"Failed to get selector information for {search_list}.", level='error')
                return False  

            selector_type, selector_value = selector_info
            # reusable_search_result_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "div.search-results-container > div > div.pv0.ph0.mb2.artdeco-card > ul")))
            reusable_search_result_list = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,selector_value)))
        except Exception as e:
            logger.log_message(f"Exception occurred while getting reusable_search_result_list {e}", level='error')
            return
        try:
            attendee_element = "reusable_search_result_list_1"
            selector_info = get_selector_info(attendee_element, selectors)

            if not selector_info:
                logger.log_message(f"Failed to get selector information for {attendee_element}.", level='error')
                return False 

            selector_type, selector_value = selector_info
            attendee_elements = reusable_search_result_list.find_elements(By.CSS_SELECTOR, "li")
        except Exception as e:
            logger.log_message(f"Exception occurred while getting attendee_elements {e}", level='error')

        for attendee_element in attendee_elements:
            logger.log_message(f"Processing an attendee element...",level='info')
            try:
                attendee_name = "attendee_name"
                selector_info = get_selector_info(attendee_name, selectors)

                if not selector_info:
                    logger.log_message(f"Failed to get selector information for {attendee_name}.", level='error')

                selector_type, selector_value = selector_info
                # name = attendee_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text
                name = attendee_element.find_element(By.CSS_SELECTOR, selector_value).text
            except Exception as e:
                name = "LinkedIn Member"
                logger.log_message(f"Exception occurred while extracting name: {e}", level='error')

            try:
                attendee_location = "attendee_location"
                selector_info = get_selector_info(attendee_location, selectors)

                if not selector_info:
                    logger.log_message(f"Failed to get selector information for {attendee_location}.", level='error')

                selector_type, selector_value = selector_info
                # location = attendee_element.find_element(By.CSS_SELECTOR, "div.linked-area.flex-1.cursor-pointer > div > div > div > div:nth-of-type(3)").text
                location = attendee_element.find_element(By.CSS_SELECTOR, selector_value).text
            except Exception as e:
                location = "Unknown Location"
                logger.log_message(f"Exception occurred while extracting location: {e}", level='error')

            try:
                attendee_occupation = "attendee_occupation" 
                selector_info = get_selector_info(attendee_occupation, selectors)

                if not selector_info:
                    logger.log_message(f"Failed to get selector information for {attendee_occupation}.", level='error')

                selector_type, selector_value = selector_info
                # occupation = attendee_element.find_element(By.CSS_SELECTOR, "div.t-14.t-black.t-normal").text
                occupation = attendee_element.find_element(By.CSS_SELECTOR, selector_value).text
            except Exception as e:
                occupation = "Unknown Occupation"
                logger.log_message(f"Exception occurred while extracting occupation: {e}", level='error')

            try:
                profile_image = "profile_image"
                selector_info = get_selector_info(profile_image, selectors)

                if not selector_info:
                    logger.log_message(f"Failed to get selector information for {profile_image}.", level='error')

                selector_type, selector_value = selector_info
                profile_image = attendee_element.find_element(By.CLASS_NAME, selector_value).get_attribute("src")
                # profile_image = attendee_element.find_element(By.CLASS_NAME, "presence-entity__image").get_attribute("src")
            except Exception as e:
                profile_image = ""
                logger.log_message(f"Exception occurred while extracting profile_image: {e}", level='error')

            try:
                profile_url = "profile_url"
                selector_info = get_selector_info(profile_url, selectors)

                if not selector_info:
                    logger.log_message(f"Failed to get selector information for {profile_url}.", level='error')

                selector_type, selector_value = selector_info
                # profile_url = attendee_element.find_element(By.CSS_SELECTOR, "div.t-roman.t-sans > div > span > span > a").get_attribute("href")
                profile_url = attendee_element.find_element(By.CSS_SELECTOR, selector_value).get_attribute("href")
            except Exception as e:
                profile_url = "Unknown Profile URL"
                logger.log_message(f"Exception occurred while extracting profile_url: {e}", level='error')

            attendee = {
                "sddh_id": sddh_id,
                "name": name,
                "location": location,
                "occupation": occupation,
                "profile_url": profile_url,
                "profile_image": profile_image,
                "linkedin_link": linkedin_link,
                "company_linkedin_url": company_linkedin_url,
                "source": scraping_mode,
                "error_reason": error_reason
            }
            save_attendee_data(attendee)
    except Exception as e:
        logger.log_message(f"Exception occurred while finding reusable_search_result_list: {e}", level='error')


