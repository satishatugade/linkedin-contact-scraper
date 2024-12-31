from flask import Blueprint, request, jsonify
import json
from service.categories import classify_event, grabL1Category 
import utils.logging as logger 
from service.l1_model import train_l1_model  
from service.l2_model import train_l2_models 
fetch_categories_blueprint = Blueprint('fetch_categories', __name__)
l1_model_blueprint = Blueprint('model', __name__)
l2_model_blueprint = Blueprint('l2_model', __name__)

@l1_model_blueprint.route('/api/l1-train-model', methods=['POST'])
def L1_train_model():
    try:
        
        logger.log_message(f"Starting L1 model training", level='info')
        train_l1_model()
        logger.log_message(f"Successfully trained and saved L1 model", level='info')
        return jsonify({"message": "L1 model trained and saved successfully"}), 200
    except Exception as e:

        logger.log_message(f"Error training L1 model: {str(e)}", level='error')
        return jsonify({"error": str(e)}), 500


@l2_model_blueprint.route('/api/l2-train-model', methods=['POST'])
def L2_train_model_api():
    try:
        
        logger.log_message(f"Starting L2 model training via API", level='info')
        train_l2_models()
        logger.log_message(f"Successfully trained and saved L2 models", level='info')
        return jsonify({"message": "L2 models trained and saved successfully"}), 200

    except Exception as e:
       
        logger.log_message(f"Error training L2 models: {str(e)}", level='error')
        return jsonify({"error": str(e)}), 500

@fetch_categories_blueprint.route('/api/fetch-categories', methods=['POST'])
def fetch_categories():
    try:
        logger.log_message(f"Starting category prediction via API", level='info')
        data = request.get_json()
        event_name = data.get('event_name')
        event_desc = data.get('event_description')

        if not event_name.strip() or not event_desc.strip():
            return jsonify({"error": "Both 'event name' and 'event description' are required."}), 400

        category = grabL1Category(event_name, event_desc)
  
        logger.log_message(f"Successfully predicted categories", level='info')
        return jsonify({"message": "Prediction successful", "category": json.loads(category)}), 200

    except Exception as e:
        logger.log_message(f"Error during prediction: {str(e)}", level='error')
        return jsonify({"error": str(e)}), 500

@fetch_categories_blueprint.route('/api/classify', methods=['POST'])
def classify():
    try:
        data = request.get_json()
        event_name = data.get('event_name')
        event_desc = data.get('event_description')

        if not event_name or not event_desc:
            return jsonify({"error": "Both 'eventName' and 'eventDesc' are required."}), 400
        
        description=f"{event_name} {event_desc}"
        result = classify_event(description)
        return jsonify({"data":result,"error":None })
    except Exception as e:
        logger.log_message(message=f"Exception while getting L1/L2 tags {e}", level="error")
        return jsonify({"data":None,"error":f"Exception while getting L1/L2 tags {e}" })
