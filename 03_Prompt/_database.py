from ExternalFiles._common_file import COMMON_FILE
from _cryptography import CRYPTOGRAPHY
from _utils import *
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from sklearn.feature_extraction.text import TfidfVectorizer
import json
import pickle
import os
import shutil
from _tokenizer import TOKENIZER
from _config import CONFIG
config = CONFIG()

class DATABASE:
    def __init__(self):
        self.CommonFiles = COMMON_FILE()
        self.cryptography = CRYPTOGRAPHY(config.key_path)

    def save_external_files(self, json_data, document_path, document_name):
        docs = []
        if '.pdf' in document_name or '.doc' in document_name or '.pptx' in document_name:
            docs.extend(self.CommonFiles.myLoader(json_data, document_path, document_name))
        else:
            print('Error: file format of ' + document_name + ' is not supported')
            return

        split = MyTextSplitter()
        split.run(docs, 500, '\n*\n')
        split.run(docs, 500, '*\n')
        split.run(docs, 500, '\n')

        content_array = [doc.page_content for doc in docs]
        metadata_array = [doc.metadata for doc in docs]

        simplified_content_array = list(range(len(content_array)))
        for i in range(len(content_array)):
            simplified_content_array[i] = simplifyData(content_array[i])
    
        # path = f'{config.data}external/{document_id}'
        path = f'{config.data}{document_path}'
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except OSError as e:
                print(f"An error occurred while creating the directory '{path}': {e}")

        content_array = self.cryptography.encode_array(content_array)
        self.save_data_json(content_array,metadata_array, f'{path}/data.json')
        self.save_TFIDF_vector(simplified_content_array, path)

    def save_data_json(self, texts, metadata, path):
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
    
    def save_TFIDF_vector(self, variable, path):
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

    def delete_external_files(self, document_path):
        path = f'{config.data}{document_path}'
        if os.path.exists(path):
            shutil.rmtree(path)
        else:
            print('Warning: folder is not existed')

class MyTextSplitter:
    def __init__(self):
        self.Tokenizer = TOKENIZER()

    def run(self, document, max_token_length, separator):
        remove_list = []
        for i in range(len(document)):
            doc = document[i]
            token_length = self.Tokenizer.tokenizer(doc.page_content, return_tensors='pt').input_ids.size(1)
            if token_length > max_token_length:
                remove_list.append(doc)
                metadata = doc.metadata
                texts = doc.page_content.split(separator)
                start = 0
                end = 0
                while end <= len(texts):
                    _token_length = 0
                    while _token_length <= max_token_length and end <= len(texts):
                        end += 1
                        text = ('\n*\n').join(texts[start:end])
                        _token_length = self.Tokenizer.tokenizer(text, return_tensors='pt').input_ids.size(1)
                    page_content = ('\n*\n').join(texts[start:end-1])
                    _token_length = self.Tokenizer.tokenizer(page_content, return_tensors='pt').input_ids.size(1)
                    if _token_length > max_token_length:
                        if config.debug:
                            print('Warning: token length exceed max token |', str(_token_length))
                    if page_content != '':
                        if metadata['section_name'] != '' and start != 0:
                            page_content = metadata['section_name'] + '\n' + page_content
                        document.extend([Document(page_content=page_content, metadata=metadata)])
                    start = end - 1
        for item in remove_list:
            document.remove(item)
        
