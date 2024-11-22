from flask import Blueprint, jsonify, request
from service.excel_processor import excel_to_db_postgres, process_l1_tags, process_l2_tags
import utils.logging as logger
import os
from dotenv import load_dotenv

load_dotenv()
excel_blueprint = Blueprint('excel', __name__)

@excel_blueprint.route('/api/generate-taxonomy', methods=['POST'])
def generate_taxonomy_database():
    try:
        logger.log_message(f"Started processing Excel files", level='info')
        l1_file = request.files.get('l1')
        l2_file = request.files.get('l2')
      
        if not l1_file or not l2_file:
            logger.log_message(f"Both 'l1' and 'l2' files are required", level='error')
            return jsonify({"error": "Both 'l1' and 'l2' files are required"}), 400
       
        temp_dir = './temp'
        os.makedirs(temp_dir, exist_ok=True)

        l1_file_path = os.path.join(temp_dir, l1_file.filename)
        l1_file.save(l1_file_path)

        l2_file_path = os.path.join(temp_dir, l2_file.filename)
        l2_file.save(l2_file_path)

        resultL1 = process_l1_tags(l1_file_path)
        resultL2 = process_l2_tags(l2_file_path)
        if resultL1['error'] is None and resultL2['error'] is None:
            return jsonify({"message": "L1 and L2 Tags bulk uploaded","error":None}), 200
        return jsonify({"message": "Error uploading taxonomy","error":f"Error L1: {resultL1['error']} L2: {resultL2['error']}"}), 500

    except Exception as e:
        logger.log_message(f"Error processing Excel files", level='error', error=str(e))
        return jsonify({"error": str(e)}), 500
