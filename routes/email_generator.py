# from flask import Blueprint, jsonify
# from service.email_generating import generate_emails_for_contacts

# email_generator_bp = Blueprint('email_generator', __name__)

# # Define an API route that processes the email generation
# @email_generator_bp.route('/api/generate-emails', methods=['POST'])
# def generate_emails():
#     result = generate_emails_for_contacts()
#     return jsonify(result)
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


@email_generator_bp.route('/api/get-email-data', methods=['POST'])
def get_domain_data():
    # Retrieve query parameters from the request
    data = request.get_json()
    dom = data.get('domain')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    api_key = os.getenv("HUNTER_API_KEY")
    api_url = os.getenv("HUNTER_API_URL")

    # Build the URL with parameters
    url = f"{api_url}?domain={dom}&first_name={first_name}&last_name={last_name}&api_key={api_key}"
    
    # Send GET request to the external API
    print(url)
    response = requests.get(url)
    if response.status_code == 200:
        # Parse and return the JSON data from the response
        data = response.json()
        return jsonify(data)
    else:
        # Return an error message with the response status code
        return jsonify({"error": "Failed to retrieve data", "status_code": response.status_code}), response.status_code
