import pandas as pd
import psycopg2
from psycopg2 import sql
import config.database_config as db
import utils.logging as logger

def excel_to_db_postgres(file, table_name):
    """Processes and saves the uploaded Excel file to a specified database table."""
    conn = db.database_connection()
    cursor = conn.cursor()

    sheets = pd.read_excel(file, sheet_name=None)
    df = pd.concat(sheets.values(), ignore_index=True)
    
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    drop_table_query = sql.SQL("DROP TABLE IF EXISTS {}").format(sql.Identifier(table_name))
    cursor.execute(drop_table_query)

    columns = ", ".join([f"{col} TEXT" for col in df.columns])
    create_table_query = sql.SQL("CREATE TABLE {} ({})").format(sql.Identifier(table_name), sql.SQL(columns))
    cursor.execute(create_table_query)
    for _, row in df.iterrows():
        insert_query = sql.SQL("INSERT INTO {} VALUES ({})").format(
            sql.Identifier(table_name),
            sql.SQL(',').join(map(sql.Literal, row))
        )
        cursor.execute(insert_query)

    conn.commit()
    cursor.close()
    conn.close()
    logger.log_message(f"Table {table_name} created and data inserted successfully.", level="info")

def process_l1_tags(file):
    try:
        df = pd.read_excel(file)
        data = [(row['phrase'], row['label']) for index, row in df.iterrows()]
        
        if bulk_insert_l1(data):
            return {"message": f"Successfully inserted {len(data)} rows.", "error": None}
        else:
            return {"message": "Error occurred during L1 bulk insert.", "error": "Bulk insert failed"}
    except Exception as e:
        logger.log_message(message=f"Exception while processing L1 tags: {e}", level="error")
        return {"message": f"Exception while processing L1 tags {e}", "error": str(e)}

def bulk_insert_l1(data):
    try:
        with db.database_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO l1_tags (phrase, label)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING
                """
                cur.executemany(query, data)
                conn.commit()
        return True
    except Exception as e:
        logger.log_message(message=f"Error in bulk insert for L1: {e}", level="error")
        return False

def process_l2_tags(file):
    try:
        df = pd.read_excel(file)
        data = [(row['phrase'], row['label'], row['L1_category']) for index, row in df.iterrows()]
        
        if bulk_insert_l2(data):
            return {"message": f"Successfully inserted {len(data)} rows.", "error": None}
        else:
            return {"message": "Error occurred during L2 bulk insert.", "error": "Bulk insert failed"}
    except Exception as e:
        logger.log_message(message=f"Exception while processing L2 tags: {e}", level="error")
        return {"message": f"Exception while processing L2 tags {e}", "error": str(e)}


def bulk_insert_l2(data):
    try:
        with db.database_connection() as conn:
            with conn.cursor() as cur:
                query = """
                    INSERT INTO l2_tags (phrase, label, l1_category)
                    VALUES (%s, %s,%s)
                    ON CONFLICT DO NOTHING
                """
                cur.executemany(query, data)
                conn.commit()
        return True
    except Exception as e:
        logger.log_message(message=f"Error in bulk insert for L2: {e}", level="error")
        return False
