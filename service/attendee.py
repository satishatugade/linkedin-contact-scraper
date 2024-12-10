import config.database_config as DB
import utils.logging as logger
import time
import os
import psycopg2

def save_attendee_data(attendee):
    """Save scraped attendee data to the database."""
    db_conn = DB.database_connection()
    if not db_conn:
        logger.log_message(f"Failed to connect to the database",level='info')
        return "failed"
    
    try:
        with db_conn.cursor() as cursor:
            insert_query = """
            INSERT INTO uq_event_contact_info (sddh_id, contact_name, occupation, location, profile_url, linkedin_url, company_url, source, error_reason)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (
                attendee['sddh_id'],
                attendee['name'],
                attendee['occupation'],
                attendee['location'],
                attendee['profile_url'],
                attendee['linkedin_url'],  # Now saving the linkedin_url
                attendee['company_url'],    # Company URL
                attendee['source'],         # Scraping mode (selenium or ocr)
                attendee['error_reason']    # Error reason if any
            ))

            update_scraping_state_query = """
                UPDATE uq_data_dump_details
                SET datapoint_value = 'true'
                WHERE sddh_id = %s AND datapoint_name = 'LinkedInScrapingState'
            """
            cursor.execute(update_scraping_state_query, (attendee['sddh_id'],))
        
        db_conn.commit()
        logger.log_message(f"Attendee data saved successfully for sddh_id: {attendee['sddh_id']}",level='info')
        return "success"
    except psycopg2.Error as e:
        logger.log_message(f"Error saving data to PostgreSQL: {e}",level='info')
        return "failed"
    finally:
        if db_conn:
            db_conn.close()

def fetch_all_selectors():
    """
    Fetch all element selectors from the database and return them in a structured format.
    """
    db_conn = DB.database_connection()
    if not db_conn:
        logger.log_message(f"Failed to connect to the database", level='error')
        return None 

    try:
        cursor = db_conn.cursor()
        query = "SELECT element_name, selector_type, selector_value FROM uq_contact_element_mapping"
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()
        db_conn.close()

        if not results:
            logger.log_message("No selectors found in the database", level='warning')
            return {} 
        selectors = {
            row[0]: {'selector_type': row[1], 'selector_value': row[2]} for row in results
        }
        return selectors

    except Exception as e:
        logger.log_message(f"Error fetching selectors from the database: {str(e)}", level='error')
        if db_conn:
            db_conn.close()     
        return None  
  
def get_selector_info(element_name, selectors):
    try:
        if element_name not in selectors:
            logger.log_message(f"Selector for {element_name} not found in the selectors dictionary.", level='error')
            return None

        selector_info = selectors[element_name]
        selector_type = selector_info['selector_type']
        selector_value = selector_info['selector_value']

        return selector_type, selector_value
    
    except Exception as e:
        logger.log_message(f"Error retrieving selector info for {element_name}: {str(e)}", level='error')
        return None

