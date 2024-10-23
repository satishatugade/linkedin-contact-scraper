# from flask import Blueprint, jsonify
# from service.email_generating import generate_emails_for_contacts

# email_generator_bp = Blueprint('email_generator', __name__)

# # Define an API route that processes the email generation
# @email_generator_bp.route('/api/generate-emails', methods=['POST'])
# def generate_emails():
#     result = generate_emails_for_contacts()
#     return jsonify(result)
import threading
from flask import Blueprint, jsonify
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
