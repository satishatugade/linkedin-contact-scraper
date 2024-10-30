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
