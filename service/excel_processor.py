import os
import pandas as pd
import psycopg2
from psycopg2 import sql

def excel_to_db_postgres(excel_file, db_params):
    table_name = os.path.splitext(os.path.basename(excel_file))[0].lower()

    try:
        
        conn = psycopg2.connect(
            dbname=db_params['dbname'],
            user=db_params['user'],
            password=db_params['password'],
            host=db_params['host'],
            port=db_params['port']
        )
        cursor = conn.cursor()

     
        sheets = pd.read_excel(excel_file, sheet_name=None)
        df = pd.concat(sheets.values(), ignore_index=True)

        drop_table_query = f"DROP TABLE IF EXISTS {table_name};"
        cursor.execute(drop_table_query)

        df_columns = df.columns.tolist()
        columns = ", ".join([f"{col} TEXT" for col in df_columns])
        create_table_query = f"CREATE TABLE {table_name} ({columns});"
        cursor.execute(create_table_query)

        
        for _, row in df.iterrows():
            insert_query = sql.SQL("INSERT INTO {} VALUES ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(map(sql.Literal, row))
            )
            cursor.execute(insert_query)

        
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        raise Exception(f"Error processing file {excel_file}: {e}")
