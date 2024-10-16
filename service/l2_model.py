import pandas as pd
from sqlalchemy import create_engine
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
import pickle
import os
from dotenv import load_dotenv
import config.database_config as DB
import utils.logging as logger
 
load_dotenv()

def fetch_data_from_db():
    try:
        logger.log_message(f"Fetching data from the database", level='info')
        db_params = DB.load_database_config()

        if not all([db_params.get('dbname'), db_params.get('user'), db_params.get('password'), db_params.get('host'), db_params.get('port')]):
            raise ValueError("Database credentials are missing from the configuration")
        engine = create_engine(f"postgresql://{db_params['user']}:{db_params['password']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}")
       
        query = "SELECT phrase, label, l1_category FROM l2_tags"
        df = pd.read_sql(query, engine)
        logger.log_message(f"Data fetched successfully", level='info')
        return df

    except Exception as e:
        logger.log_message(f"Error fetching data from the database", level='error', error=str(e))
        raise
        

# Analyze and save the model for each l1_category
def analyze_and_save_model(df, l1_category):
    try:
        logger.log_message(f"Training model for l1_category: {l1_category}", level='info')

        df_filtered = df[df['l1_category'] == l1_category]

        if df_filtered.empty:
            logger.log_message(f"No data found for l1_category = '{l1_category}'", level='error')
            return
        
        X = df_filtered['phrase']
        y = df_filtered['label']

        vectorizer = TfidfVectorizer()
        X_vect = vectorizer.fit_transform(X)

        X_train, X_test, y_train, y_test = train_test_split(X_vect, y, test_size=0.2, random_state=42)

        model = LogisticRegression(max_iter=500)
        param_grid = {'C': [0.1, 1, 10, 100], 'solver': ['liblinear', 'saga']}

        grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy')
        grid_search.fit(X_train, y_train)

        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test)

        logger.log_message(f"Best model parameters for {l1_category}: {grid_search.best_params_}", level='info')
        logger.log_message(f"Model evaluation for {l1_category}:\n{classification_report(y_test, y_pred)}", level='info')

        # Save the model and vectorizer
        model_filepath = os.getenv('L2_MODEL_SAVE_PATH', './models/L2')
        vectorizer_filepath = os.getenv('L2_VECTORIZER_FILE_PATH_SAVE', './models/L2')

        model_filepath = fr'{model_filepath}/logistic_regression_model_{l1_category}.pkl'
        vectorizer_filepath = fr'{vectorizer_filepath}/tfidf_vectorizer_{l1_category}.pkl'
        os.makedirs(os.path.dirname(model_filepath), exist_ok=True)
        os.makedirs(os.path.dirname(vectorizer_filepath), exist_ok=True)

        with open(model_filepath, 'wb') as model_file:
            pickle.dump(best_model, model_file)

        with open(vectorizer_filepath, 'wb') as vectorizer_file:
            pickle.dump(vectorizer, vectorizer_file)

        logger.log_message(f"Model saved to {model_filepath}", level='info')
        logger.log_message(f"Vectorizer saved to {vectorizer_filepath}", level='info')
    
    except Exception as e:
        logger.log_message(f"Error training model for {l1_category}: {str(e)}", level='error')

# Train models for all l1_category
def train_l2_models():
    try:
        logger.log_message(f"Starting training for all L2 models", level='info')

        df = fetch_data_from_db()

        required_columns = ['phrase', 'label', 'l1_category']
        if not all(column in df.columns for column in required_columns):
            raise ValueError(f"The database table must contain the following columns: {required_columns}")

        unique_l1_categories = df['l1_category'].unique()
        for l1_category in unique_l1_categories:
            analyze_and_save_model(df, l1_category)

        logger.log_message(f"Training for all L2 models completed", level='info')

    except Exception as e:
        logger.log_message(f"Error during L2 model training: {str(e)}", level='error')
        raise
