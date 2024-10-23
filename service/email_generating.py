import requests
import psycopg2
import config.database_config as db  # Reuse the existing database config
import utils.logging as logger

api_key = "87fc6ba5420f4eac3fa10713bcfbd9ef44494fa4"

def split_name(full_name):
    """Splits the full name into first and last name."""
    parts = full_name.strip().split(" ", 1)
    return parts[0], parts[1] if len(parts) > 1 else ''

def generate_email_and_update(first_name, last_name, domain, full_name, cursor, conn):
    """Generates emails using Hunter API and updates the database."""
    if domain and first_name:
        domains = domain.split(",")  
        emails = []

        for dom in domains:
            dom = dom.strip()  
            url = f"https://api.hunter.io/v2/email-finder?domain={dom}&first_name={first_name}&last_name={last_name}&api_key={api_key}"
            response = requests.get(url)
            data = response.json()

            if response.status_code == 200 and 'data' in data and 'email' in data['data']:
                email = data['data']['email']
                emails.append(email)
                logger.log_message(f"Generated email for {full_name} with domain {dom}: {email}", level="info")
            else:
                logger.log_message(f"Failed to generate email for {full_name} with domain {dom}: {data.get('errors', 'Unknown error')}", level="error")
        emails = [email for email in emails if email is not None]

        if emails:
            emails_str = ", ".join(emails)  
            update_query = """
            UPDATE uq_event_contact_info
            SET email = %s
            WHERE contact_name = %s
            """
            cursor.execute(update_query, (emails_str, full_name))
            conn.commit()
        else:
            logger.log_message(f"No valid emails found for {full_name}", level="info")
    else:
        logger.log_message(f"No domain found for {full_name}", level="error")

def generate_emails_for_contacts():
    """Main function to fetch contacts, generate emails, and update the database."""
    conn = db.database_connection()
    if conn is None:
        return {"status": "error", "message": "Database connection failed"}

    cursor = conn.cursor()

    # Manual test entries for demonstration (can be removed in production)
    manual_entries = [
        ("akshada kothavale", "catseyetech.in, example.com"),
        ("shavez ansari", "catseyetech.in, example.org, example.net")
    ]

    for full_name, domain in manual_entries:
        first_name, last_name = split_name(full_name)
        generate_email_and_update(first_name, last_name, domain, full_name, cursor, conn)

    # Fetch contacts from the database and process them
    query = "SELECT contact_name, domain FROM uq_event_contact_info"
    cursor.execute(query)

    for (full_name, domain) in cursor.fetchall():
        first_name, last_name = split_name(full_name)
        generate_email_and_update(first_name, last_name, domain, full_name, cursor, conn)

    cursor.close()
    conn.close()

    return {"status": "success", "message": "Email generation completed"}
