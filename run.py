from flask import Flask,jsonify
from flask_cors import CORS
from routes.category_controller import l2_model_blueprint
from routes.category_controller import l1_model_blueprint
from routes.category_controller import fetch_categories_blueprint
from routes.contacts_controller import contact_scraper_bp
from routes.excel_controller import excel_blueprint
from routes.ocr_controller import ocr_blueprint
# from routes.google_searching_controller import google_domain_search_blueprint
from utils.logging import setup_logging

setup_logging()

app = Flask(__name__)
CORS(app)
# app = create_app()

app.register_blueprint(l2_model_blueprint)
app.register_blueprint(l1_model_blueprint)
app.register_blueprint(fetch_categories_blueprint)
app.register_blueprint(contact_scraper_bp)
app.register_blueprint(excel_blueprint)
app.register_blueprint(ocr_blueprint)
# app.register_blueprint(google_domain_search_blueprint)
@app.route('/', methods=['GET'])
def getHome():
    return {"message": "Contacts server is running..."}

if __name__ == '__main__':
    app.run(debug=True, port=5005,host="0.0.0.0")
