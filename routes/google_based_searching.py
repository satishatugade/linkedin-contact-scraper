from flask import Blueprint,request, jsonify
from config.database_config import database_connection
from service.google_fetching_linkedin_profile import process_contacts
from service.domain_name_searching import process_company_data
import utils.logging as logger
import requests
import os

linkedin_bp = Blueprint('linkedin_profileurl_google', __name__)

@linkedin_bp.route('/api/fetch-profile-data', methods=['POST'])
def scrape_linkedin_profiles():
    # Establish database connection
    db_connection = database_connection()
    
    if not db_connection:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = db_connection.cursor()

    try:
        # Fetch contacts with missing LinkedIn profile URLs
        cursor.execute("SELECT id, contact_name, occupation FROM uq_event_contact_info WHERE profile_url IS NULL")
        contacts = cursor.fetchall()

        if contacts:
            process_contacts(contacts, cursor, db_connection)  # Process the contacts
            message = f"Successfully scraped {len(contacts)} profiles."
            logger.log_message(message, level="info")
            return jsonify({"status": "success", "message": message}), 200
        else:
            message = "No contacts with missing LinkedIn profile URLs."
            logger.log_message(message, level="info")
            return jsonify({"status": "success", "message": message}), 200

    except Exception as e:
        logger.log_message(f"Error during LinkedIn profile scraping: {str(e)}", level="error")
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        db_connection.close()

company_bp = Blueprint('domain_company_google', __name__)

@company_bp.route('/api/search-domain', methods=['POST'])
def process_companies():
    logger.log_message("Received request to process companies", level="info")

    try:
        # Call the function to process company data
        result = process_company_data()

        if result:
            message = "Successfully processed company data."
            logger.log_message(message, level="info")
            return jsonify({"status": "success", "message": message, "data": result}), 200
        else:
            message = "Failed to process company data."
            logger.log_message(message, level="error")
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.log_message(f"Error processing companies: {str(e)}", level="error")
        return jsonify({"status": "error", "message": str(e)}), 500
    
@company_bp.route('/api/get-domain', methods=['POST'])
def get_domain_data():
    try:
        data = request.get_json()
        CLEARBIT_API_KEY = os.getenv('CLEARBIT_API_KEY')
        CLEARBIT_API_URL = os.getenv('CLEARBIT_API_URL')
        company_name = data.get('company_name')
        headers = {'Authorization': f'Bearer {CLEARBIT_API_KEY}'}
    
        api_url = f'{CLEARBIT_API_URL}{company_name}'
        response = requests.get(api_url, headers=headers)
                
        if response.status_code == 200:
            response=response.json()
            return jsonify({"data":{"domain":response.get("domain"),"logo":response.get("logo")},"error":None}),200
        else:
            response=response.json()
            return jsonify({"data":None,"error":response.get("error")}),400
    except Exception as e:
        print(e)
        return jsonify({"data":None,"error":{"message":f"{e}","type":f"Exception occurs"}}),500
