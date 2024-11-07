from flask import Blueprint,request, jsonify
from config.database_config import database_connection
from service.google_fetching_linkedin_profile import process_contacts
from routes.email_generator import fetch_email_data
from service.domain import process_company_data
import utils.logging as logger
import requests
import os

linkedin_bp = Blueprint('linkedin_profileurl_google', __name__)

@linkedin_bp.route('/api/fetch-profile-data', methods=['POST'])
def scrape_linkedin_profiles():
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
        data = request.get_json()
        sddh_id= data.get("sddh_id")
        result = process_company_data(sddh_id)

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
    
def fetch_company_domain(company_name):
    """Fetch company domain and logo from Clearbit API."""
    try:
        CLEARBIT_API_KEY = os.getenv('CLEARBIT_API_KEY')
        CLEARBIT_API_URL = os.getenv('CLEARBIT_API_URL')
        headers = {'Authorization': f'Bearer {CLEARBIT_API_KEY}'}
        api_url = f'{CLEARBIT_API_URL}{company_name}'

        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return {"domain": data.get("domain"), "logo": data.get("logo")}, None
        else:
            error = response.json().get("error")
            return None, error

    except Exception as e:
        return None, {"message": str(e), "type": "Exception occurs"}

@company_bp.route('/api/get-domain', methods=['POST'])
def get_domain_data():
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        result, error = fetch_company_domain(company_name)
        if error:
            return jsonify({"data": None, "error": error}), 400
        else:
            return jsonify({"data": result, "error": None}), 200

    except Exception as e:
        print(e)
        return jsonify({"data": None, "error": {"message": str(e), "type": "Exception occurs"}}), 500

@company_bp.route('/api/get-company-info', methods=['POST'])
def get_company_info():
    data = request.get_json()
    profile_url = data.get('profile_url')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    api_key = os.getenv('SCRAPIN_API_KEY')
    url = os.getenv('SCRAPIN_API_URL')

    if not profile_url:
        return jsonify({"error": "Profile url parameter are required"}), 400

    querystring = {
        "apikey": api_key,
        "linkedInUrl": profile_url
    }

    try:
        response = requests.get(url, params=querystring)
        response.raise_for_status() 
        response_data  = response.json() 
        person_data = response_data.get('person', {})
        positions = person_data.get('positions', {}).get('positionHistory', [])
        company_data = response_data.get('company', {})
        industry = company_data.get('industry')

        first_position = positions[0] if positions else {}
        company_name = first_position.get("companyName")

        domain_info, error = fetch_company_domain(company_name) if company_name else (None, None)
        if error:
            logger.log_message(f"Clearbit fetch domain having error : {error}")

        domain = domain_info.get("domain") if domain_info else ""
        if domain:
            email_result, email_error = fetch_email_data(domain, first_name, last_name)
            if email_error:
                logger.log_message(f"Hunter fetch email of person having error : {email_error}")
            email = email_result.get("data", {}).get("email") if email_result else ""
        else:
            email_result = None
        first_position = {
            "company_location": positions[0].get("companyLocation"),
            "company_logo": positions[0].get("companyLogo"),
            "company_name": positions[0].get("companyName"),
            "industry": industry,
            "domain": domain,
            "email": email
        } if positions else {}

        return jsonify({"data": first_position,"scrapin_api_dump": response_data })

    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500
