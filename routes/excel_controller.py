from flask import Blueprint, jsonify, request
from app.excel_processor import excel_to_db_postgres
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

        
        db_params = {
            "dbname": os.getenv("DB_NAME"),
            "user": os.getenv("DB_USER"),
            "password": os.getenv("DB_PASSWORD"),
            "host": os.getenv("DB_HOST"),
            "port": os.getenv("DB_PORT")
        }

        excel_to_db_postgres(l1_file_path, db_params)
        excel_to_db_postgres(l2_file_path, db_params)

        logger.log_message(f"Successfully processed L1 and L2 files", level='info')

        return jsonify({"message": "Both L1 and L2 Excel files processed successfully"}), 200

    except Exception as e:
        logger.log_message(f"Error processing Excel files", level='error', error=str(e))
        return jsonify({"error": str(e)}), 500
