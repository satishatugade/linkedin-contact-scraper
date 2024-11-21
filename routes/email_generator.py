import threading
from flask import Blueprint, jsonify,request
import requests
import os
from service.email_generating import generate_emails_for_contacts
from service.domain import fetch_company_domain
from utils.logging import log_message


email_generator_bp = Blueprint('email_generator', __name__)

def threaded_email_generation():
    result = generate_emails_for_contacts()
    return result

@email_generator_bp.route('/api/generate-emails', methods=['POST'])
def generate_emails():
    
    email_thread = threading.Thread(target=threaded_email_generation)
    email_thread.start()
    return jsonify({"message": "Email generation started in the background"}), 202


def fetch_email_data(domain, first_name, last_name):
    """Fetch email data from Hunter API."""
    try:
        api_key = os.getenv("HUNTER_API_KEY")
        api_url = os.getenv("HUNTER_API_URL")

        url = f"{api_url}?domain={domain}&first_name={first_name}&last_name={last_name}&api_key={api_key}"
        response = requests.get(url)

        if response.status_code == 200:
            return response.json(), None
        else:
            return None, {"message": "Failed to retrieve data", "status_code": response.status_code}

    except requests.exceptions.RequestException as e:
        return None, {"message": str(e), "type": "RequestException"}

@email_generator_bp.route('/api/get-email-data', methods=['POST'])
def get_email_data_info():

    try:
        data = request.get_json()
        # domain = data.get('domain')
        log_message(level='info',message=f"Input request forget_email_data_info : {data}")
        company_name = data.get('company_name')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        clearbit_response, error = fetch_company_domain(company_name)
        log_message(level='info',message=f"clearbit_response {clearbit_response}")
        if error:            
            log_message(level='error',message=f"Error in fetch company domain :{error}")
            return jsonify({"error": error,"data":{"first_name":first_name,"last_name":last_name,"domain":None,"email":None}}), 400
        else:
            result, error = fetch_email_data(clearbit_response.get('domain'), first_name, last_name)
            result["data"]["company_logo"] =clearbit_response.get('logo')
            result["data"]["domain"] =clearbit_response.get('domain')
            result["data"]["first_name"]=first_name
            result["data"]["last_name"]=last_name
            if error:
                return jsonify({"error": error,"data":{"first_name":first_name,"last_name":last_name,"domain":None,"email":None}}), error.get("status_code", 500)
            else:
                return jsonify(result), 200
    except Exception as e:
        log_message(level='error',message=f"Error in fetch email info api :{e}")
        return jsonify({"error": {"message": f"Error in fetch email info api :{e}","type": "Exception"},"data":{"first_name":first_name,"last_name":last_name,"domain":None,"email":None}}),500
