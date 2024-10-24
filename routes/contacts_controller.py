from flask import Blueprint, request, jsonify
import utils.logging as logger
# from concurrent.futures import ThreadPoolExecutor
import threading
from routes.linkedin_scraper import process_event_page, fetch_linkedin_url_dump_detail_table
# from controllers.linkedin_scraper import process_event_page, getLinkFromContactInfo, fetch_sddh_by_id

contact_scraper_bp = Blueprint('scraper', __name__)

@contact_scraper_bp.route('/api/linkedin-contacts-scraper', methods=['POST'])
def scrape_linkedin_atteendees_data():
    data = request.get_json()
    session_id = data.get('session_id')
    li_at_value = data.get('li_at_value')
    scraping_mode = data.get('scraping_mode', '').lower()
    sddh_id = data.get('sddh_id')
    logger.log_message(f"Event Id given for scraping {sddh_id}")

    if not session_id or not li_at_value:  
        logger.log_message(f"session_id and li_at_value are required")
        return jsonify({'error': 'session Id and token is required'}), 400

    linkedin_url_list = fetch_linkedin_url_dump_detail_table(sddh_id)
    if linkedin_url_list == "failed":
        logger.log_message("Failed to retrieve LinkedIn links from the database",level='info')
        return jsonify({'error': 'Linkedin links not found'}), 500

    print(f"linkedin_url_list count : ",len(linkedin_url_list))
    logger.log_message(f"linkedin_url_list count : ",len(linkedin_url_list))

    for data in linkedin_url_list:
        threading.Thread(
        target=process_event_page,
        args=(data.company_linkedin_url, sddh_id, scraping_mode, session_id, li_at_value)).start()
    
    logger.log_message(f"Linkedin contact scraping started !",level='info')
    return jsonify({'message': 'Linkedin contact scraping started !'}), 200

