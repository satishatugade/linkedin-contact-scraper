from flask import Blueprint, request, jsonify
import utils.logging as logger
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from routes.linkedin_scraper import process_event_page, fetch_linkedin_url_dump_detail_table
# from controllers.linkedin_scraper import process_event_page, getLinkFromContactInfo, fetch_sddh_by_id
import time

contact_scraper_bp = Blueprint('scraper', __name__)

@contact_scraper_bp.route('/api/linkedin-contacts-scraper', methods=['POST'])
def scrape_linkedin():
   
    data = request.get_json()

    session_id = data.get('session_id')
    li_at_value = data.get('li_at_value')
    scraping_mode = data.get('scraping_mode', '').lower()
    sddh_id = data.get('sddh_id')
    logger.log_message(f"Logging in")
    print(sddh_id)
    logger.log_message(f"siddh_id given {sddh_id}")

    # Check for required session_id and li_at_value
    if not session_id or not li_at_value:
        
        logger.log_message(f"session_id and li_at_value are required")
        return jsonify({'error': 'session Id and token is required'}), 400

    # Set up Selenium options
    options = Options()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    options.add_argument('--ignore-certificate-errors')

    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 30)

    # Set LinkedIn cookies
    driver.get("https://www.linkedin.com/")
    driver.add_cookie({'name': 'JSESSIONID', 'value': session_id})
    driver.add_cookie({'name': 'li_at', 'value': li_at_value})
    time.sleep(5)

    
    logger.log_message("No specific sddh_id provided or sddh_id is null, scraping all records.")
    # Fetch all LinkedIn links if no specific sddh_id is provided or if sddh_id is "null"
    # contact_info_list = get_link_from_contact_info()
    contact_info_list = fetch_linkedin_url_dump_detail_table(sddh_id)
    if contact_info_list == "failed":
        logger.log_message("Failed to retrieve LinkedIn links from the database",level='info')
        return jsonify({'error': 'Failed to retrieve LinkedIn links from the database'}), 500

    for contact_info in contact_info_list:
        process_event_page(driver, wait, contact_info.linkdin_link, contact_info.sddh_id, scraping_mode)

    driver.quit()
    logger.log_message(f"Scraping completed successfully",level='info')
    return jsonify({'message': 'Scraping completed successfully'}), 200

