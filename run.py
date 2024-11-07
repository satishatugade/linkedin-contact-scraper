from flask import Flask,jsonify
from flask_cors import CORS
from dotenv import load_dotenv
from routes.category_controller import l2_model_blueprint
from routes.category_controller import l1_model_blueprint
from routes.category_controller import fetch_categories_blueprint
from routes.contacts_controller import contact_scraper_bp
from routes.excel_controller import excel_blueprint
from routes.ocr_controller import ocr_blueprint
from utils.logging import setup_logging
from routes.google_based_searching import linkedin_bp
from routes.google_based_searching import company_bp
from routes.email_generator import email_generator_bp
setup_logging()
load_dotenv()

app = Flask(__name__)
CORS(app)
app.register_blueprint(l2_model_blueprint)
app.register_blueprint(l1_model_blueprint)
app.register_blueprint(fetch_categories_blueprint)
app.register_blueprint(contact_scraper_bp)
app.register_blueprint(excel_blueprint)
app.register_blueprint(ocr_blueprint)
app.register_blueprint(linkedin_bp)
app.register_blueprint(email_generator_bp)
app.register_blueprint(company_bp)
@app.route('/', methods=['GET'])
def getHome():
    return {"message": "Contacts server is running..."}

if __name__ == '__main__':
    app.run(debug=True, port=5005,host="0.0.0.0")
