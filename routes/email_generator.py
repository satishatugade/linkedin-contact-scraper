import threading
from flask import Blueprint, jsonify,request
import requests
import os
from service.email_generating import generate_emails_for_contacts

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
    data = request.get_json()
    domain = data.get('domain')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    result, error = fetch_email_data(domain, first_name, last_name)
    if error:
        return jsonify({"error": error}), error.get("status_code", 500)
    else:
        return jsonify(result), 200