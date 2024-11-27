import pickle
import json
from dotenv import load_dotenv
import os
import utils.logging as logger 
# from sklearn.metrics.pairwise import cosine_similarity
# from sentence_transformers import SentenceTransformer
from utils.constants import l1_tags,l2_tags,stopwords

# model = SentenceTransformer('all-MiniLM-L6-v2')

def get_contributing_features(vectorizer, input_vect):
    feature_names = vectorizer.get_feature_names_out()
    non_zero_indices = input_vect.nonzero()[1]
    feature_contributions = [(feature_names[idx], input_vect[0, idx]) for idx in non_zero_indices]
    sorted_contributions = sorted(feature_contributions, key=lambda x: x[1], reverse=True)
    return sorted_contributions

def remove_stopwords(text):
    words = text.split()
    filtered_words = [word for word in words if word.lower() not in stopwords]
    return ' '.join(filtered_words)

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
    eventName=remove_stopwords(eventName)
    eventDesc=remove_stopwords(eventDesc)
    loaded_model, loaded_vectorizer = load_model_and_vectorizer(model_filename, vectorizer_filename)
    
    combined_input = f"{eventName} {eventDesc}".lower().replace(" the ","").replace(" a ","").replace(" to ","").replace(" of ","").replace(" a ","").replace(" an ","").replace(" in ","").replace(" and ","")
    logger.log_message(message=f"combined_input : {combined_input}",level="info")
    data = [combined_input]
    X_test_vect = loaded_vectorizer.transform(data)
    y_pred = loaded_model.predict(X_test_vect)

    contributions = get_contributing_features(loaded_vectorizer, X_test_vect)
    for word, score in contributions:
        logger.log_message(level="info", message=f"Word: {word}, Score: {score}")
    
    feature_names = loaded_vectorizer.get_feature_names_out()
    non_zero_indices = X_test_vect.nonzero()[1]
    contributing_words = [feature_names[idx] for idx in non_zero_indices]
    logger.log_message(message=f"Contributing words for predictions {y_pred} {contributing_words}",level="info")
    L1 = y_pred[0]
    L2 = grabL2Category(eventDesc, L1)

    result = {
        "L1": L1,
        "L2": L2,
        "L3": ""
    }

    return json.dumps(result)

# def precompute_embeddings(tags):
#     return {tag: model.encode(tag) for tag in tags}

# l1_embeddings = precompute_embeddings(l1_tags.keys())
# l2_embeddings = precompute_embeddings(l2_tags.keys())

# def classify_event(description):
#     description_embedding = model.encode(description)
#     # Level 1 matching: Find the best match for Level 1 tags
#     level_1_tag = None
#     level_1_score = 0
#     l1_reason = ""
#     for keyword, tag_embedding in l1_embeddings.items():
#         score = cosine_similarity([description_embedding], [tag_embedding])[0][0]
#         if score > level_1_score:
#             level_1_score = score
#             level_1_tag = l1_tags[keyword]
#             l1_reason = keyword
#             logger.log_message(message=f"score: {score} | tag: {level_1_tag} | keyword: {keyword}")

#     # Filter L2 tags based on the chosen L1 tag
#     filtered_l2_tags = {
#         keyword: tags
#         for keyword, tags in l2_tags.items()
#         if level_1_tag in tags
#     }
#     # Level 2 matching: Find the best match for Level 2 tags
#     level_2_tag = None
#     level_2_score = 0
#     l2_reason = ""
#     for keyword, tags in filtered_l2_tags.items():
#         score = cosine_similarity([description_embedding], [l2_embeddings[keyword]])[0][0]
#         if score > level_2_score:
#             level_2_score = score
#             level_2_tag = tags
#             l2_reason = keyword

#     return {
#         "level_1_tag": level_1_tag,
#         "level_2_tag": level_2_tag,
#         "level_1_reason": l1_reason,
#         "level_2_reason": l2_reason
#     }

