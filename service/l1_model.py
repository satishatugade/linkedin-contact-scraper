import pandas as pd
from sqlalchemy import create_engine
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.preprocessing import StandardScaler
import pickle
import os
from dotenv import load_dotenv
import utils.logging as logger 
import config.database_config as DB
load_dotenv()

def fetch_data_from_db():
    try:
        logger.log_message(f"Fetching data from the database", level='info')
        engine= DB.database_connection()

        
        query = "SELECT phrase, label FROM L1_tags"
        df = pd.read_sql(query, engine)
        logger.log_message(f"Data fetched successfully", level='info')
        return df

    except Exception as e:
        logger.log_message(f"Error fetching data from the database", level='error', error=str(e))
        raise


def train_l1_model():
    try:
        logger.log_message(f"Starting L1 model training process", level='info')
        df = fetch_data_from_db()

        if 'phrase' not in df.columns or 'label' not in df.columns:
            raise ValueError("The database table must contain 'phrase' and 'label' columns.")
        X = df['phrase']
        y = df['label']
        vectorizer = TfidfVectorizer()
        X_vect = vectorizer.fit_transform(X)
        scaler = StandardScaler(with_mean=False)
        X_vect_scaled = scaler.fit_transform(X_vect)
        X_train, X_test, y_train, y_test = train_test_split(X_vect_scaled, y, test_size=0.2, random_state=42)
        model = LogisticRegression(max_iter=1000)
        param_grid = {'C': [0.1, 1, 10, 100], 'solver': ['liblinear', 'saga']}
        grid_search = GridSearchCV(model, param_grid, cv=5, scoring='accuracy')
        grid_search.fit(X_train, y_train)

        
        best_model = grid_search.best_estimator_
        y_pred = best_model.predict(X_test)

        logger.log_message(f"Best model parameters: {grid_search.best_params_}", level='info')
        logger.log_message(f"Model training completed", level='info')
        logger.log_message(f"Model evaluation:\n{classification_report(y_test, y_pred)}", level='info')
        model_filename = os.getenv('L1_MODEL_SAVE_PATH', './models/L1/logistic_regression_model.pkl')
        vectorizer_filename = os.getenv('L1_VECTORIZER_FILE_PATH_SAVE', './models/L1/tfidf_vectorizer.pkl')
        os.makedirs(os.path.dirname(model_filename), exist_ok=True)
        os.makedirs(os.path.dirname(vectorizer_filename), exist_ok=True)

        with open(model_filename, 'wb') as model_file:
            pickle.dump(best_model, model_file)
        with open(vectorizer_filename, 'wb') as vectorizer_file:
            pickle.dump(vectorizer, vectorizer_file)
        logger.log_message(f"Model saved to {model_filename}", level='info')
        logger.log_message(f"Vectorizer saved to {vectorizer_filename}", level='info')
    
    except Exception as e:
        logger.log_message(f"Error during L1 model training", level='error', error=str(e))
        raise
