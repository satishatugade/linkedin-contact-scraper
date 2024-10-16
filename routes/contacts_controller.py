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
def scrape_linkedin_atteendees_data():
    data = request.get_json()
    session_id = data.get('session_id')
    li_at_value = data.get('li_at_value')
    scraping_mode = data.get('scraping_mode', '').lower()
    sddh_id = data.get('sddh_id')
    logger.log_message(f"Logging in")
    print(sddh_id)
    logger.log_message(f"sddh_id given {sddh_id}")

    # Check for required session_id and li_at_value
    if not session_id or not li_at_value:  
        logger.log_message(f"session_id and li_at_value are required")
        return jsonify({'error': 'session Id and token is required'}), 400
    
    driver = webdriver.Chrome()
    wait = WebDriverWait(driver, 30)

    # Set LinkedIn cookies
    driver.get("https://www.linkedin.com/")
    driver.add_cookie({'name': 'JSESSIONID', 'value': session_id})
    driver.add_cookie({'name': 'li_at', 'value': li_at_value})
    driver.refresh()
    time.sleep(5)

    linkedin_url_list = fetch_linkedin_url_dump_detail_table(sddh_id)
    if linkedin_url_list == "failed":
        logger.log_message("Failed to retrieve LinkedIn links from the database",level='info')
        return jsonify({'error': 'Failed to retrieve LinkedIn links from the database'}), 500

    print(f"linkedin_url_list ",linkedin_url_list)
    for data in linkedin_url_list:
        process_event_page(driver, wait, data.company_linkdin_link, data.sddh_id, scraping_mode)

    driver.quit()
    logger.log_message(f"Scraping completed successfully",level='info')
    return jsonify({'message': 'Scraping completed successfully'}), 200

