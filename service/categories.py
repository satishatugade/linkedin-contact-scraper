import pickle
import json
from dotenv import load_dotenv
import os

def load_model_and_vectorizer(model_path, vectorizer_path):
    with open(model_path, 'rb') as model_file:
        loaded_model = pickle.load(model_file)
    
    with open(vectorizer_path, 'rb') as vectorizer_file:
        loaded_vectorizer = pickle.load(vectorizer_file)
    
    return loaded_model, loaded_vectorizer

def grabL2Category(eventDesc, L1Category):
    load_dotenv()
    model_filepath = os.getenv('L2_MODEL_PATH', r'D:\Setup\pyTools\models\L2')
    vectorizer_filepath = os.getenv('L2_VECTORIZER_PATH', r'D:\Setup\pyTools\models\L2')

    model_filepath = f'{model_filepath}\\logistic_regression_model_{L1Category}.pkl'
    vectorizer_filepath = f'{vectorizer_filepath}\\tfidf_vectorizer_{L1Category}.pkl'

    try:
        loaded_model, loaded_vectorizer = load_model_and_vectorizer(model_filepath, vectorizer_filepath)
        
        if loaded_model is None or loaded_vectorizer is None:
            return ""  # Return an empty string if the L2 model or vectorizer is not loaded

        data = [eventDesc]
        X_test_vect = loaded_vectorizer.transform(data)
        predictions = loaded_model.predict(X_test_vect)

        L2 = predictions[0]
        return L2  # Return the L2 prediction if the model is loaded correctly
    except FileNotFoundError:
        return ""
    
def grabL1Category(eventName, eventDesc):
    load_dotenv()
    model_filename = os.getenv('L1_MODEL_PATH', r'D:\Setup\pyTools\models\L1\L1_model.pkl')
    vectorizer_filename = os.getenv('L1_VECTORIZER_PATH', r'D:\Setup\pyTools\models\L1\l1_vectorizer.pkl')

    loaded_model, loaded_vectorizer = load_model_and_vectorizer(model_filename, vectorizer_filename)

    data = [eventDesc]
    X_test_vect = loaded_vectorizer.transform(data)
    y_pred = loaded_model.predict(X_test_vect)

    L1 = y_pred[0]
    L2 = grabL2Category(eventDesc, L1)

    result = {
        "L1": L1,
        "L2": L2,
        "L3": ""
    }

    return json.dumps(result)
