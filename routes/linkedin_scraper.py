import utils.logging as logger
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os
import psycopg2
# from config.database_config as config
from config import database_config as DB


class ContactInfo:
    """Class to represent LinkedIn contact information."""
    def __init__(self, sddh_id, linkdin_link):
        self.sddh_id = sddh_id
        self.linkdin_link = linkdin_link

def fetch_sddh_by_id(sddh_id):
    conn = DB.database_connection()
    if not conn:
        return None

    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT sddh_id, datapoint_value AS linkdin_link
            FROM uq_data_dump_details
            WHERE datapoint_name = 'LinkedinURL' AND sddh_id = %s;
        """, (sddh_id,))
        result = cursor.fetchone()
        if result:
            return ContactInfo(result[0], result[1])
        else:
            return None
    except psycopg2.Error as e:
        logger.log_message(f"Failed to fetch sddh_id {sddh_id}:",level='error')
        return None
    finally:
        if conn:
            cursor.close()
            conn.close()
            
def fetch_linkedin_url_dump_detail_table(sddh_id):
    db_conn = DB.database_connection()
    if not db_conn:
        print("Failed to connect to the database")
        return "failed"
    try:
        cursor = db_conn.cursor()
        query = """SELECT uddd1.sddh_id, uddd1.datapoint_value AS linkedin_link
                   FROM uq_data_dump_details uddd1
                   JOIN uq_data_dump_details uddd2
                   ON uddd1.sddh_id = uddd2.sddh_id
                   WHERE uddd1.datapoint_name = 'LinkedinURL'
                   AND uddd2.datapoint_name = 'LinkedInScrapingState'
                   AND uddd2.datapoint_value = 'false'"""
        if sddh_id != "":
            query += " AND uddd1.sddh_id = %s"
            cursor.execute(query, (sddh_id,))
        else:
            cursor.execute(query)
        results = cursor.fetchall()   
        contact_info_list = [ContactInfo(row[0], row[1]) for row in results]
        return contact_info_list

    except Exception as e:
        print(f"Failed to execute query: {e}")
        return "failed"
    finally:
        if db_conn:
            cursor.close()
            db_conn.close()   
    #     if sddh_id and sddh_id.strip() != "":
    #         query += " AND uddd1.sddh_id = %s"
    #         cursor.execute(query, (sddh_id,))
    #     else:
    #         cursor.execute(query)
            
    #     results = cursor.fetchall()
    #     contact_info_list = [ContactInfo(row[0], row[1]) for row in results]
    #     return contact_info_list
    # except Exception as e:
    #     print(f"Failed to execute query: {e}")
    #     return "failed"
    # finally:
    #     if db_conn:
    #         cursor.close()
    #         db_conn.close()
    # db_conn = DB.database_connection()
    # if not db_conn:
    #     print("Failed to connect to the database")
    #     return "failed"
    # try:
    #     cursor = db_conn.cursor()
    #     query = """SELECT uddd1.sddh_id, uddd1.datapoint_value AS linkedin_link
    #                 FROM uq_data_dump_details uddd1
    #                 JOIN uq_data_dump_details uddd2
    #                 ON uddd1.sddh_id = uddd2.sddh_id
    #                 WHERE uddd1.datapoint_name = 'LinkedinURL'
    #                 AND uddd2.datapoint_name = 'LinkedInScrapingState'
    #                 AND uddd2.datapoint_value = 'false'
    #                 """
    #     # if sddhId != "":
    #     #     query += " AND uddd1.sddh_id = %s"
    #     #     cursor.execute(query, (sddhId,))
    #     # else:
    #     #     cursor.execute(query)
    #     if sddhId is not None and sddhId != "":
    #         query += "AND uddd1.sddh_id = %s"
    #         logger.log_message(f"Query: {query}, Params: {sddhId}", level='info')
    #         cursor.execute(query, (sddhId,))
    #     else:
    #         logger.log_message("Fetching all records, no specific sddh_id provided", level='info')
    #         cursor.execute(query)
        
    #     results = cursor.fetchall()   
    #     contact_info_list = [ContactInfo(row[0], row[1]) for row in results]
    #     return contact_info_list

    # except Exception as e:
    #     print(f"Failed to execute query: {e}")
    #     return "failed"
    # finally:
    #     if db_conn:
    #         cursor.close()
    #         db_conn.close()

# def get_link_from_contact_info():
#     """Fetch LinkedIn URLs for all unprocessed records from the database."""
#     conn = DB.database_connection()
#     if not conn:
#         return "failed"

#     try:
#         cursor = conn.cursor()
#         cursor.execute("""
#             SELECT uddd1.sddh_id, uddd1.datapoint_value AS linkdin_link
#             FROM uq_data_dump_details uddd1
#             JOIN uq_data_dump_details uddd2 ON uddd1.sddh_id = uddd2.sddh_id
#             WHERE uddd1.datapoint_name = 'LinkedinURL' AND uddd2.datapoint_name = 'LinkedInScrapingState'
#             AND uddd2.datapoint_value = 'false';
#         """)
#         results = cursor.fetchall()
#         return [ContactInfo(row[0], row[1]) for row in results]
#     except Exception as e:
#         logger.log_message(f"Failed to execute query:",level='error')
#         return "failed"
#     finally:
#         if conn:
#             cursor.close()
#             conn.close()

def save_attendee_data(attendee):
    """Save scraped attendee data to the database."""
    db_conn = DB.database_connection()
    if not db_conn:
        logger.log_message(f"Failed to connect to the database",level='info')
        return "failed"
    
    try:
        with db_conn.cursor() as cursor:
            insert_query = """
            INSERT INTO uq_event_contact_info (sddh_id, contact_name, occupation, location, profile_url, linkedin_url, company_url, source, error_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                attendee['sddh_id'],
                attendee['name'],
                attendee['occupation'],
                attendee['location'],
                attendee['profile_url'],
                attendee['linkedin_url'],  # Now saving the linkedin_url
                attendee['company_url'],    # Company URL
                attendee['source'],         # Scraping mode (selenium or ocr)
                attendee['error_reason']    # Error reason if any
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
    time.sleep(10)  
    if "feed" in driver.current_url:
        logger.log_message(f"Login successful!",level='info')
        return True
    else:
        logger.log_message(f"Login unsuccessful. Current URL: {driver.current_url}",level='error')
        return False

def process_event_page(driver, wait, linkedin_event_url, sddh_id, scraping_mode):
    """Process LinkedIn event page based on scraping mode."""
    driver.get(linkedin_event_url.strip())
    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    time.sleep(5)

    linkedin_url = None  
    if click_attend_button(driver, wait):
        linkedin_url = driver.current_url  
        logger.log_message(f"Attend button found. LinkedIn URL set to: {linkedin_url}",level='info')

        # Try to click the 'Attendees' link and paginate through the attendees
        if click_attendees_link(driver, wait):
            handle_pagination(driver, wait, sddh_id, scraping_mode, linkedin_url)

    else:
        if click_attendees_link(driver, wait):
            linkedin_url = driver.current_url  # Capture the current URL
            logger.log_message(f"Attendees link found. LinkedIn URL set to: {linkedin_url}",level='info')

            handle_pagination(driver, wait, sddh_id, scraping_mode, linkedin_url)

        else:
            logger.log_message(f"Neither Attend button nor Attendees link found. Checking for upcoming events.",level='info')
            
            if click_show_all_events(driver, wait):
                event_links = get_upcoming_event_links(driver, wait)
                for event_link in event_links:
                    linkedin_url = event_link
                    logger.log_message(f"Processing upcoming event link: {event_link}",level='info')
                    process_event_page(driver, wait, event_link, sddh_id, scraping_mode)
            else:
                logger.log_message(f"No upcoming events available.",level='info')

def click_attend_button(driver, wait):
    """Attempt to click the 'Attend' button."""
    logger.log_message(f"Attempting to click the 'Attend' button",level='info')
    try:
        attend_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[3]/div[2]/div/div/main/section[1]/div[1]/div[2]/div/div[1]/div[2]/div[1]/button/span")))
        attend_button.click()
        time.sleep(5)
        logger.log_message(f"Attend button clicked successfully",level='info')
        return True
    except Exception as e:
        logger.log_message(f"Attend button not found.",level='info')
        return False

def click_attendees_link(driver, wait):
    """Attempt to click the 'Attendees' link."""
    logger.log_message(f"Attempting to click the 'Attendees' link",level='info')
    try:
        attendees_link = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a.link-without-visited-state.full-width")))
        attendees_link.click()
        time.sleep(5)
        logger.log_message(f"Attendees link clicked successfully",level='info')
        return True
    except Exception as e:
        logger.log_message(f"Attendees link not found.",level='error')
        return False

def click_show_all_events(driver, wait):
    """Attempt to click the 'Show all events' button."""
    logger.log_message(f"Attempting to click the 'Show all events' button",level='info')
    try:
        show_all_events_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "a[aria-label='Show all events']")))
        driver.execute_script("arguments[0].scrollIntoView(true);", show_all_events_button)
        time.sleep(2)
        show_all_events_button.click()
        time.sleep(5)
        logger.log_message(f"Show all events button clicked successfully",level='info')
        return True
    except Exception as e:
        logger.log_message(f"NO show all events button found' button: {e}",level='info')
        return False

def get_upcoming_event_links(driver, wait):
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

def handle_pagination(driver, wait, sddh_id, scraping_mode, linkedin_url):
    """Handle pagination for OCR or Selenium mode."""
    logger.log_message(f"Handling pagination with {scraping_mode} mode.",level='info')
    page_count = 1
    folder_name = f"{sddh_id}"
    folder_path = os.path.join(os.getcwd(), "screenshots", folder_name)
    os.makedirs(folder_path, exist_ok=True)

    if scraping_mode == 'ocr':
        # OCR Mode: Take screenshots of each page.
        while True:
            try:
                reusable_search_result_list = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "reusable-search__entity-result-list")))
                take_screenshot(driver, sddh_id, page_count, folder_path, "before_scroll")
                time.sleep(3)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                take_screenshot(driver, sddh_id, page_count, folder_path, "after_scroll")

                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-pagination__button--next")))
                    next_button.click()
                    time.sleep(6)
                    page_count += 1
                except Exception as e:
                    logger.log_message(f"No more pages or error clicking next button. Pagination ended.",level='info')
                    break
            except Exception as e:
                logger.log_message(f"Error during OCR pagination: {e}",level='error')
                break

    elif scraping_mode == 'selenium':
        # Selenium Mode: Scrape attendee data
        while True:
            try:
                reusable_search_result_list = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "reusable-search__entity-result-list")))
                attendee_elements = reusable_search_result_list.find_elements(By.CLASS_NAME, "reusable-search__result-container")

                for attendee_element in attendee_elements:
                    try:
                        name = attendee_element.find_element(By.CSS_SELECTOR, "span[aria-hidden='true']").text
                    except:
                        name = "LinkedIn Member"
                    try:
                        location = attendee_element.find_element(By.CLASS_NAME, "entity-result__secondary-subtitle").text
                    except:
                        location = "Unknown Location"
                    try:
                        occupation = attendee_element.find_element(By.CLASS_NAME, "entity-result__primary-subtitle").text
                    except:
                        occupation = "Unknown Occupation"
                    try:
                        profile_url = attendee_element.find_element(By.CSS_SELECTOR, "a.app-aware-link").get_attribute("href")
                    except:
                        profile_url = "Unknown Profile URL"

                    # Save the attendee data
                    attendee = {
                        "sddh_id": sddh_id,
                        "name": name,
                        "location": location,
                        "occupation": occupation,
                        "profile_url": profile_url,
                        "linkedin_url": linkedin_url,  # Save the LinkedIn URL
                        "company_url": company_url,    # Save the company URL
                        "source": scraping_mode,       # Save scraping mode (selenium or ocr)
                        "error_reason": ""
                    }
                    save_attendee_data(attendee)

                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)

                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.artdeco-pagination__button--next")))
                    next_button.click()
                    time.sleep(6)
                    page_count += 1
                except:
                    logger.log_message(f"No more pages or error clicking next button. Pagination ended.",level='info')
                    break
            except Exception as e:
                logger.log_message(f"Error scraping attendees:",level='error')
                break

def take_screenshot(driver, sddh_id, page_count, folder_path, prefix):
    """Take a screenshot for OCR-based processing with correct naming."""
    screenshot_path = os.path.join(folder_path, f"{sddh_id}_{prefix}_page_{page_count}.png")
    driver.save_screenshot(screenshot_path)
    logger.log_message(f"Screenshot saved: {screenshot_path}",level='info')

