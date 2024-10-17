from flask import Blueprint, jsonify, request
from service.ocr_logic import ocr_scrapping_save  
import os

ocr_blueprint = Blueprint('ocr', __name__)

@ocr_blueprint.route('/api/save-ocr-data', methods=['POST'])
def Ocr_save():
    try:
        data = request.get_json()
        root_folder = data.get('root_folder')

        if not root_folder or not os.path.exists(root_folder):
            return jsonify({"error": "Invalid or missing root folder path"}), 400

        ocr_scrapping_save(root_folder)

        return jsonify({"message": "OCR processing completed successfully"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
