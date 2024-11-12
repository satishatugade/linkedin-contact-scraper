from flask import Blueprint,request, jsonify
from config.database_config import database_connection
from service.google_fetching_linkedin_profile import process_contacts
from routes.email_generator import fetch_email_data
from service.domain import process_company_data
from utils.logging import log_message
import utils.logging as logger
import requests
import os
import traceback
import tldextract
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
from googlesearch import search


linkedin_bp = Blueprint('linkedin_profileurl_google', __name__)

@linkedin_bp.route('/api/fetch-profile-data', methods=['POST'])
def scrape_linkedin_profiles():
    db_connection = database_connection()
    
    if not db_connection:
        return jsonify({"status": "error", "message": "Database connection failed"}), 500

    cursor = db_connection.cursor()

    try:
        # Fetch contacts with missing LinkedIn profile URLs
        cursor.execute("SELECT id, contact_name, occupation FROM uq_event_contact_info WHERE profile_url IS NULL")
        contacts = cursor.fetchall()

        if contacts:
            process_contacts(contacts, cursor, db_connection)  # Process the contacts
            message = f"Successfully scraped {len(contacts)} profiles."
            logger.log_message(message, level="info")
            return jsonify({"status": "success", "message": message}), 200
        else:
            message = "No contacts with missing LinkedIn profile URLs."
            logger.log_message(message, level="info")
            return jsonify({"status": "success", "message": message}), 200

    except Exception as e:
        logger.log_message(f"Error during LinkedIn profile scraping: {str(e)}", level="error")
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        cursor.close()
        db_connection.close()

company_bp = Blueprint('domain_company_google', __name__)

@company_bp.route('/api/search-domain', methods=['POST'])
def process_companies():
    logger.log_message("Received request to process companies", level="info")

    try:
        data = request.get_json()
        sddh_id= data.get("sddh_id")
        result = process_company_data(sddh_id)

        if result:
            message = "Successfully processed company data."
            logger.log_message(message, level="info")
            return jsonify({"status": "success", "message": message, "data": result}), 200
        else:
            message = "Failed to process company data."
            logger.log_message(message, level="error")
            return jsonify({"status": "error", "message": message}), 500

    except Exception as e:
        logger.log_message(f"Error processing companies: {str(e)}", level="error")
        return jsonify({"status": "error", "message": str(e)}), 500
    
def fetch_company_domain(company_name):
    """Fetch company domain and logo from Clearbit API."""
    try:
        CLEARBIT_API_KEY = os.getenv('CLEARBIT_API_KEY')
        CLEARBIT_API_URL = os.getenv('CLEARBIT_API_URL')
        headers = {'Authorization': f'Bearer {CLEARBIT_API_KEY}'}
        api_url = f'{CLEARBIT_API_URL}{company_name}'

        response = requests.get(api_url, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            return {"domain": data.get("domain"), "logo": data.get("logo")}, None
        else:
            error = response.json().get("error")
            return None, error

    except Exception as e:
        return None, {"message": str(e), "type": "Exception occurs"}

@company_bp.route('/api/get-domain', methods=['POST'])
def get_domain_data():
    try:
        data = request.get_json()
        company_name = data.get('company_name')
        result, error = fetch_company_domain(company_name)
        if error:
            return jsonify({"data": None, "error": error}), 400
        else:
            return jsonify({"data": result, "error": None}), 200

    except Exception as e:
        print(e)
        return jsonify({"data": None, "error": {"message": str(e), "type": "Exception occurs"}}), 500
    

def extract_root_domain(url):
    try:
        extracted = tldextract.extract(url)
        root_domain = f"{extracted.domain}.{extracted.suffix}"
        return root_domain
    except Exception as e:
        print(f"Error extracting domain: {e}")
        logger.log_message(f"Error extracting domain: {e}")
        return None    

def fetch_company_data_with_scrapin_api(profile_url):
    api_key = os.getenv('SCRAPIN_API_KEY')
    url = os.getenv('SCRAPIN_API_URL')
    querystring = {
        "apikey": api_key,
        "linkedInUrl": profile_url
    }
    response = requests.get(url, params=querystring)
    response.raise_for_status() 
    response_data  = response.json() 
    return response_data

@company_bp.route('/api/get-profile-info', methods=['POST'])
def get_company_info():
    data = request.get_json()
    profile_url = data.get('profile_url')
    first_name = data.get('first_name')
    last_name = data.get('last_name')

    if not profile_url:
        return jsonify({"error": "Profile url parameter are required"}), 400
    # try:
    #     profile_data=get_linkedin_profile(profile_url)
    #     # location = profile_data["city"]
    #     profile_image = profile_data["profileImage"]
    #     company_name = profile_data["companyName"]
    #     company_url = profile_data["companyDetails"]["url"]
    #     if company_url !="":
    #         try:
    #             scraping_domain=extract_root_domain(company_url)
    #         except Exception as e:
    #             scraping_domain = "" 
    #             logger.log_message(f"Exception caught: {e}")
    #         if scraping_domain:
    #             logger.log_message(f"Scrapin domain use for hunter api to find email {scraping_domain}")
    #             email_result, email_error = fetch_email_data(scraping_domain, first_name, last_name)
    #             if email_error:
    #                 logger.log_message(f"Hunter fetch email of person having error : {email_error}")
    #             email = email_result.get("data", {}).get("email") if email_result else ""    
    #         data = {
    #                 "company_location": "",
    #                 "company_logo": "",
    #                 "company_name": company_name,
    #                 "industry": "",
    #                 "domain": "",
    #                 "scrapin_domain":scraping_domain,
    #                 "email": email,
    #                 "profile_image": profile_image
    #         } 
    #         return jsonify({"data": data,"scrapin_api_dump": None })
    # except requests.exceptions.RequestException as e:
    #         stack_trace = traceback.format_exc()
    #         logger.log_message(f"Profile scrape exception occures stack_trace : {stack_trace}")        
    #         logger.log_message(f"Profile scrape exception occures object : {e}")        

    try:
        response_data=fetch_company_data_with_scrapin_api(profile_url)
        person_data = response_data.get('person', {})
        positions = person_data.get('positions', {}).get('positionHistory', [])
        company_data = response_data.get('company', {})
        industry = company_data.get('industry')
        websiteUrl = company_data.get('websiteUrl')
        try:
            scraping_domain=extract_root_domain(websiteUrl)
        except Exception as e:
            scraping_domain = "" 
            logger.log_message(f"Exception caught: {e}")    

        first_position = positions[0] if positions else {}
        company_name = first_position.get("companyName")

        domain_info, error = fetch_company_domain(company_name) if company_name else (None, None)
        if error:
            logger.log_message(f"Clearbit fetch domain having error : {error}")

        domain = domain_info.get("domain") if domain_info else ""
        if scraping_domain:
            logger.log_message(f"Scrapin domain use for hunter api to find email {scraping_domain}: {first_name} : {last_name}")

            email_result, email_error = fetch_email_data(scraping_domain, first_name, last_name)
            if email_error:
                logger.log_message(f"Hunter fetch email of person having error : {email_error}")
            logger.log_message(f"Email data : {email_result}")
            email = email_result.get("data", {}).get("email") if email_result else ""
        else:
            logger.log_message(f"Clearbit domain use for hunter api to find email {domain}")
            email_result, email_error = fetch_email_data(domain, first_name, last_name)
            if email_error:
                logger.log_message(f"Hunter fetch email of person having error : {email_error}")
            email = email_result.get("data", {}).get("email") if email_result else ""

        first_position = {
            "company_location": positions[0].get("companyLocation"),
            "company_logo": positions[0].get("companyLogo"),
            "company_name": positions[0].get("companyName"),
            "industry": industry,
            "domain": domain,
            "scrapin_domain":scraping_domain,
            "email": email,
            "profile_image": ""
        } if positions else {}

        return jsonify({"data": first_position,"scrapin_api_dump": response_data })

    except requests.exceptions.RequestException as e:
        stack_trace = traceback.format_exc()
        logger.log_message(f"Scrapin api exception occures : {stack_trace}")   
        return jsonify({"error": str(e)}), 500

 
def getCompanyDomain(company):
    try:
        query=f"{company} website"
        results=search(query, advanced=True)
        results_list = list(results)
        logger.log_message(f"Company google search results: {results_list[0]}",level="info")   
        return results_list[0]
    except Exception as e:
        logger.log_message(f"Exception while getting Company info {e}",level="error")   
        return None
   

def get_linkedin_profile(linkedInURL):
    try:
        options = Options()
        options.add_argument("--incognito")
        driver = webdriver.Chrome(options=options)
        try:
            driver.get(linkedInURL)
            driver.maximize_window()
            time.sleep(15)
            company = name = headline = companyDetails=city= profileImage= None
            try:
                company = driver.execute_script(
                    "return document.getElementsByClassName('top-card-link__description')[0].innerText;"
                )
                if company is not None:
                    res=getCompanyDomain(company)
                    companyDetails=res
                company=company
            except Exception as e:
                logger.log_message(f"Exception when getting Company Name {e}",level="error")   
            
            try:
                name = driver.execute_script("return document.getElementsByClassName('top-card-layout__title')[0].innerText")
                name=name
            except Exception as e:
                logger.log_message(f"Exception when getting Name {e}",level="error")   
            
            try:
                headline=driver.execute_script("return document.getElementsByClassName('top-card-layout__headline')[0].innerText")
                headline=headline
            except Exception as e:
                logger.log_message(f"Exception when getting about {e}",level="error")
            
            try:
                city=driver.execute_script("return document.querySelector('.not-first-middot span').innerText;")
                city=city
            except Exception as e:
                logger.log_message(f"Exception when getting city {e}",level="error")
            
            try:
                profileImage=driver.execute_script("return document.querySelector('.top-card__profile-image').src;")
                profileImage=profileImage
            except Exception as e:
                logger.log_message(f"Exception when getting profile image {e}",level="error")
                
            
            info={  
                "companyDetails":{
                        "url":companyDetails.url,
                        "description":companyDetails.description,
                        "title":companyDetails.title
                    } if companyDetails else None,
                "companyName":company,
                "name":name,
                "city":city,
                "profileImage":profileImage,
                "headline":headline
                }
            logger.log_message(f"LinkedIn profile info: {info}",level="info")
            return info
        
        except Exception as e:
            logger.log_message(f"Error while loading linkedin Profile: {e}",level="error")
            return None
        finally:
            driver.quit()
    except Exception as e:
        logger.log_message(message=f"",level="error")
        return None



@company_bp.route('/api/get-linkedin-profile',methods=['POST'])
def getLinkedinProfile():
    try:
        data=request.json
        if not data:
            return jsonify({"error": "Invalid JSON format"}), 400
        if 'profile_url' not in data:
            return jsonify({"data":None,"error":"profile_url is required"})
        info=get_linkedin_profile(data['profile_url'])
        return jsonify({"data":info})
    except Exception as e:
        return jsonify({"data":None,"error":f"Exception occured while searching link {e}"}),500

