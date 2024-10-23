# from flask import Blueprint, jsonify
# from config.database_config import database_connection
# from service.google_fetching_linkedin_profile import process_contacts
# from service.domain_name_searching import process_company_data
# import utils.logging as logger



# linkedin_bp = Blueprint('linkedin_profileurl_google', __name__)

# @linkedin_bp.route('/api/google_fetching_profile_url', methods=['GET'])
# def scrape_linkedin_profiles():
#     db_connection = database_connection()
    
#     if not db_connection:
#         return jsonify({"status": "error", "message": "Database connection failed"})

#     cursor = db_connection.cursor()
#     cursor.execute("SELECT id, contact_name, occupation FROM uq_event_contact_info WHERE profile_url IS NULL")
#     contacts = cursor.fetchall()

#     process_contacts(contacts, cursor, db_connection)

#     cursor.close()
#     db_connection.close()

#     return jsonify({"status": "success", "message": "Scraping complete!"})


# company_bp = Blueprint('domain_company_google', __name__)

# @company_bp.route('/api/domain_searching', methods=['GET'])
# def process_companies():
#     logger.log_message("Received request to process companies", level="info")
#     result = process_company_data()
#     if result:
#         logger.log_message("Successfully processed companies", level="info")
#     else:
#         logger.log_message("Failed to process companies", level="error")
#     return jsonify(result)

from flask import Blueprint, jsonify
from config.database_config import database_connection
from service.google_fetching_linkedin_profile import process_contacts
from service.domain_name_searching import process_company_data
import utils.logging as logger

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