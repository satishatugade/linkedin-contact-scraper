import pickle
import json
from dotenv import load_dotenv
import os
import utils.logging as logger 
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer
from utils.constants import l1_tags,l2_tags

model = SentenceTransformer('all-MiniLM-L6-v2')

def load_model_and_vectorizer(model_path, vectorizer_path):
    with open(model_path, 'rb') as model_file:
        loaded_model = pickle.load(model_file)
    
    with open(vectorizer_path, 'rb') as vectorizer_file:
        loaded_vectorizer = pickle.load(vectorizer_file)
    
    return loaded_model, loaded_vectorizer

def grabL2Category(eventDesc, L1Category):
    model_filepath = os.getenv('L2_MODEL_PATH')
    vectorizer_filepath = os.getenv('L2_VECTORIZER_PATH')

    model_filepath = f'{model_filepath}\\logistic_regression_model_{L1Category}.pkl'
    vectorizer_filepath = f'{vectorizer_filepath}\\tfidf_vectorizer_{L1Category}.pkl'

    try:
        loaded_model, loaded_vectorizer = load_model_and_vectorizer(model_filepath, vectorizer_filepath)
        
        if loaded_model is None or loaded_vectorizer is None:
            logger.log_message(level="info",message="L2 model or vectorizer is not loaded")
            return ""  # Return an empty string if the L2 model or vectorizer is not loaded

        data = [eventDesc]
        X_test_vect = loaded_vectorizer.transform(data)
        feature_names = loaded_vectorizer.get_feature_names_out()
        non_zero_indices = X_test_vect.nonzero()[1]
        contributing_words = [feature_names[idx] for idx in non_zero_indices]
        print("Contributing words for prediction L2:", contributing_words)
        predictions = loaded_model.predict(X_test_vect)

        L2 = predictions[0]
        return L2  # Return the L2 prediction if the model is loaded correctly
    except FileNotFoundError:
        logger.log_message(level="info",message="File Not Found Error")
        return ""
    
def grabL1Category(eventName, eventDesc):
    load_dotenv()
    model_filename = os.getenv('L1_MODEL_PATH', r'D:\eventible-git\linkedin-contact-scraper\models\L1\L1_model.pkl')
    vectorizer_filename = os.getenv('L1_VECTORIZER_PATH', r'D:\eventible-git\linkedin-contact-scraper\models\L1\l1_vectorizer.pkl')

    loaded_model, loaded_vectorizer = load_model_and_vectorizer(model_filename, vectorizer_filename)
    
    combined_input = f"{eventName} {eventDesc}"
    data = [combined_input]
    X_test_vect = loaded_vectorizer.transform(data)
    y_pred = loaded_model.predict(X_test_vect)

    feature_names = loaded_vectorizer.get_feature_names_out()
    non_zero_indices = X_test_vect.nonzero()[1]
    contributing_words = [feature_names[idx] for idx in non_zero_indices]
    print("Contributing words for prediction L1:", contributing_words)
    L1 = y_pred[0]
    L2 = grabL2Category(eventDesc, L1)

    result = {
        "L1": L1,
        "L2": L2,
        "L3": ""
    }

    return json.dumps(result)

def precompute_embeddings(tags):
    return {tag: model.encode(tag) for tag in tags}

l1_embeddings = precompute_embeddings(l1_tags.keys())
l2_embeddings = precompute_embeddings(l2_tags.keys())

def classify_event(description):
    description_embedding = model.encode(description)
    # Level 1 matching: Find best match for Level 1 tags
    level_1_tag = None
    level_1_score = 0
    l1_reson=""
    for keyword, tag_embedding in l1_embeddings.items():
        score = cosine_similarity([description_embedding], [tag_embedding])[0][0]
        if score > level_1_score:
            level_1_score = score
            level_1_tag = l1_tags[keyword]
            
    # Level 2 matching: Find best match for Level 2 tags
    level_2_tags = []
    level_2_score = 0
    for keyword, tags in l2_tags.items():
        score = cosine_similarity([description_embedding], [l2_embeddings[keyword]])[0][0]
        if score > level_2_score:
            level_2_score = score
            level_2_tags = tags

    return level_1_tag, level_2_tags

