from flask import Blueprint, jsonify, request
from app.ocr_logic import main  
import os

ocr_blueprint = Blueprint('ocr', __name__)

@ocr_blueprint.route('/api/save-ocr-data', methods=['POST'])
def Ocr_save():
    try:
        # Get the root folder path from the request
        data = request.get_json()
        root_folder = data.get('root_folder')

        if not root_folder or not os.path.exists(root_folder):
            return jsonify({"error": "Invalid or missing root folder path"}), 400

        # Call the main function from ocr_logic.py to process the OCR
        main(root_folder)

        return jsonify({"message": "OCR processing completed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
