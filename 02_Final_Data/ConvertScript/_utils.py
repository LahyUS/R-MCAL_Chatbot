import os
from cryptography.fernet import Fernet
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json
import pickle
import shutil
import nltk
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import re
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Union
from packaging import version
from _config import CONFIG
config = CONFIG()

def convertLowerCase(text):
    return text.casefold()

def removeExtraSpaces(text):
    text = text.strip()
    text = ' '.join(text.split())
    return text

def removeUndefinedCharacter(text):
    list_of_undefined_character = ['\xa0', '[', ']', '\u00a0', '\t', '\u2308', '\u230b', '()']
    for character in list_of_undefined_character:
        text = text.replace(character,'')
    return text

def lemmatizationAndStemming(text):
    tokens = word_tokenize(text)
    lemmatizer = WordNetLemmatizer()
    lemmatized_tokens = [lemmatizer.lemmatize(token) for token in tokens]
    stemmer = PorterStemmer()
    stemmed_tokens = [stemmer.stem(token) for token in tokens]
    return " ".join(stemmed_tokens)

def removeStopWords(text):
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words("english"))
    filtered_tokens = [token for token in tokens if token.lower() not in stop_words]
    filtered_text = " ".join(filtered_tokens)
    return filtered_text

def replaceCharacter(text):
    pattern = r"\b([a-zA-Z\d]+)-([a-zA-Z\d]+)\b"
    text = re.sub(pattern, r"\1_\2", text)
    return text

def simplifyData(text):
    text = convertLowerCase(text)
    text = removeExtraSpaces(text)
    text = removeUndefinedCharacter(text)
    # text = lemmatizationAndStemming(text)
    text = removeStopWords(text)
    return text

def rawData(text):
    text = removeExtraSpaces(text)
    text = removeUndefinedCharacter(text)
    return text

def simplifyQuestion(text):
    text = simplifyData(text)
    text = text.replace('?','')
    return text

def keepUniqueCharacter(array):
    unique_chars = []
    seen_chars = set()

    for char in array:
        if char not in seen_chars:
            unique_chars.append(char)
            seen_chars.add(char)

    return unique_chars

def generate_encryption_key(save_path):
    encryption_key = Fernet.generate_key()
    print('encryption_key:', encryption_key)
    with open(save_path, 'wb') as key_file:
        key_file.write(encryption_key)

def load_encryption_key(path):
    with open(path, 'rb') as key_file:
        encryption_key = key_file.read()
    return encryption_key

def encrypt_and_save(variable, path):
    encryption_key = load_encryption_key(config.key_path)
    cipher_suite = Fernet(encryption_key)
    encrypted_data = cipher_suite.encrypt(bytes(str(variable), 'utf-8'))
    with open(path, 'wb') as file:
        file.write(encrypted_data)

def save_TFIDF_vector(variable, path):
    vectorizer = TfidfVectorizer()
    vectorized_texts = vectorizer.fit_transform(variable)
    # Save the vectorizer
    vectorizer_path = path + '/vectorizer_TFIDF.pkl'
    with open(vectorizer_path, 'wb') as file:
        pickle.dump(vectorizer, file)
    # Save the vectorized_texts
    vectorized_texts_path = path + '/vectorized_texts_TFIDF.pkl'
    with open(vectorized_texts_path, 'wb') as file:
        pickle.dump(vectorized_texts, file)

def encode_text(content_array):
    encryption_key = load_encryption_key(config.key_path)
    cipher_suite = Fernet(encryption_key)
    ecrypted_content = []
    for content in content_array:
        ecrypted_content.append(cipher_suite.encrypt(content.encode()).decode())
    return ecrypted_content

def decode_text(text):
    return text

def save_data_json(texts, metadata, path):
    # folder_path = ('/').join(element for element in path.split('/')[:-1])
    data = {
        "document": []
    }
    for text, meta in zip(texts, metadata):
        content_obj = {
            "content": text,
            "metadata": meta
        }
        data["document"].append(content_obj)
    with open(path, 'w') as file:
        json.dump(data, file, indent=4)

def replicate_folder_structure(input_folder, output_folder):
    # Walk through the input folder recursively
    for root, dirs, files in os.walk(input_folder):
        # Create the corresponding subdirectories in the output folder
        for dir in dirs:
            input_dir_path = os.path.join(root, dir)
            output_dir_path = os.path.join(output_folder, os.path.relpath(input_dir_path, input_folder))
            os.makedirs(output_dir_path, exist_ok=True)