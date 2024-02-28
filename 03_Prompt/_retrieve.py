from sklearn.metrics.pairwise import cosine_similarity
import os
import pickle
import json
from _cryptography import CRYPTOGRAPHY
from _utils import *
import yaml
from _config import CONFIG
config = CONFIG()

class RETRIEVE:
    def __init__(self):
        self.cryptography = CRYPTOGRAPHY(config.key_path)
        if config.retriever == 'TFIDF':
            self.vectorizer_name = 'vectorizer_TFIDF.pkl'
            self.vectorized_texts_name = 'vectorized_texts_TFIDF.pkl'
        self.threshold = config.threshold

    def child_folder(self, path, document, question, number_of_query):
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                self.child_folder(item_path, document, question, number_of_query)
            else:
                # Seek for vectorizer file
                if item_path.endswith(self.vectorizer_name):
                    #parent_path = ('/').join(element for element in item_path.split('/')[:-1])
                    vectorizer_path = item_path
                    vectorized_texts_path = path + '/' + self.vectorized_texts_name

                    # Load vectorizer from pickle file
                    with open(vectorizer_path, 'rb') as file: 
                        vectorizer = pickle.load(file)
                    # Load vectorized_texts from pickle file
                    with open(vectorized_texts_path, 'rb') as file: 
                        vectorized_texts = pickle.load(file)

                    # TFIDF Algorithm Runv
                    ## Pre-process and compute TF-IDF value for the question 
                    vectorized_keywords = vectorizer.transform([simplifyQuestion(question)])
                    ## Get cosine similarity score vector of vectorized texts and vectorized question
                    similarity_scores = cosine_similarity(vectorized_keywords, vectorized_texts)[0]

                    # Filter out the scores
                    match_indices = list(range(len(similarity_scores)))
                    ## Thresholding the scores
                    filtered_similarity_scores = [score for score in similarity_scores if score > self.threshold]
                    ## Thresholding the indices
                    filtered_match_indices = [index for index, score in zip(match_indices, similarity_scores) if score > self.threshold]
                     
                    if len(filtered_similarity_scores) > 0:
                        # Sort the documents by similarity scores
                        sorted_pairs = sorted(zip(filtered_similarity_scores, filtered_match_indices), reverse=True)
                        # Get the top scores
                        top_similarity_scores, top_match_indices = zip(*sorted_pairs)

                        if len(top_match_indices) > number_of_query: # Cut down the extra score and indices
                            top_similarity_scores = top_similarity_scores[:number_of_query]
                            top_match_indices = top_match_indices[:number_of_query]

                        for index in range(len(top_match_indices)): # Add the satisfied document to the return list
                            document.append(path + '||' + str(top_match_indices[index]) + '||' + str(top_similarity_scores[index]))

    def get_index_data(self, document, number_of_query, keyword_list):
        index_data = []
        # Get the similarity value of the handled document
        similarity_scores = [float(element.split('||')[2]) for element in document]

        # Get indices of the top similarity documents
        if len(document) > number_of_query:
            top_match_indices = sorted(range(len(similarity_scores)), key=lambda i: similarity_scores[i], reverse=True)[:number_of_query]
        else:
            top_match_indices = sorted(range(len(similarity_scores)), key=lambda i: similarity_scores[i], reverse=True)
        top_document = [document[index] for index in top_match_indices]
        
        summary_top_document = []
        for element in top_document:
            # Extracts the parent path from the stored list
            paths = [part.split('||')[0] for part in summary_top_document] 
            # Extracts the parent path from the current element 
            path = element.split('||')[0] 

            if path in paths:  # Checks if the current path is already present in the paths list.
                index = element.split('||')[1]
                similarity = element.split('||')[2]
                # If the current path is already present in paths, 
                # appends the index and similarity to the corresponding element in summary_top_document.
                summary_top_document[paths.index(path)] += ',' + index + '||' + similarity
            else:
                summary_top_document.append(element)

        # Iterate through the document list, extract fields: folder path, information, index
        for element in summary_top_document:
            folder_path = element.split('||')[0]
            information = element.split(folder_path + '||')[1]
            list_of_information = information.split(',')
            index_number = [part.split('||')[0] for part in list_of_information]
            #scores = [part.split('||')[1] for part in list_of_information]
                    
            # With the extracted information above, obtain data from the JSON file
            with open(folder_path + '/data.json', 'r') as file:
                json_data = json.load(file)
                for number in index_number:
                    # Get data content with the specific index
                    text = json_data['document'][int(number)]['content']
                    # Decode content if any
                    if config.need_decode:
                        text = self.cryptography.decode_text(text)
                    
                    count = 0
                    # If there is not any matched keyword, the indexed data is consider to be a not good information
                    for keyword in keyword_list:
                        if keyword.lower() in text.lower():
                            count += 1
                    if count == 0:
                        continue
                    
                    # Update the decoded content into the 'content' field
                    json_data['document'][int(number)]['content'] = text
                    # Utilize JSON format, so append the json_data into the return index_data list
                    index_data.append(json_data['document'][int(number)])

        return index_data

    def obtainMetadata(self, metadatas:list):
        # Handle Metadata
        reference_links_set = set()
        wkproduct_links_set = set()
        guideline_links_set = set()
        guidelines_set = set()

        for metadata in metadatas:
            # Obtain metadata from metadata list
            path = metadata['path']
            page = metadata['page']
            wkproduct_link = metadata['wkproduct_link']
            guideline_link = metadata['guideline_link']
            section_name = metadata['section_name']
            guideline = metadata['guideline']

            # Handle reference links
            reference_links_set.add(path + '|' + page)
            # Handle work-product links
            if isinstance(wkproduct_link, list):
                if len(wkproduct_link[0]) > 1:
                    wkproduct_links_set.update(wkproduct_link)
            elif len(wkproduct_link) > 1: # string case
                wkproduct_links_set.add(wkproduct_link)
            
            # Handle guideline links
            if isinstance(guideline_link, list):
                for sublist in guideline_link:
                    if isinstance(sublist, list):
                        if len(sublist[0]) > 1:
                            guideline_links_set.update(sublist)
                    elif len(sublist) > 1: # string case
                        guideline_links_set.add(guideline_link)
            elif len(guideline_link) > 1: # string case
                guideline_links_set.add(guideline_link)

            # Handle detailed guideline
            if isinstance(guideline, list):
                final_guideline = f'***{section_name}:\n'
                for sublist in guideline:
                    if isinstance(sublist, list):
                        for g in sublist:
                            if len(g) > 1:  # Check if the string is not one character
                                final_guideline = final_guideline + g + '\n'
                    elif len(sublist) > 1:
                        final_guideline =  final_guideline + sublist + '\n'
                guidelines_set.add(final_guideline)
            elif len(guideline) > 1:
                final_guideline = f'***{section_name}:\n{guideline}'
                guidelines_set.add(final_guideline)

        # Convert sets to lists. # Cut down list if it exceed the required length
        reference_links = list(reference_links_set)[:min(config.link_number, len(reference_links_set))]
        wkproduct_links = list(wkproduct_links_set)[:min(config.link_number, len(wkproduct_links_set))]
        guideline_links = list(guideline_links_set)[:min(config.link_number, len(guideline_links_set))]
        guidelines = list(guidelines_set)[:min(config.link_number, len(guidelines_set))]
        
        return reference_links, wkproduct_links, guideline_links, guidelines

    def run(self, path, question, keyword_list, number_of_query):
        if number_of_query <= 0: return [], [], "", "", ""
        path = config.data + path

        document = []
        # Iterate through the vectorized text documents to find the matching data
        self.child_folder(path, document, question, number_of_query)
        # With the matched data, get its content from JSON file
        index_data = self.get_index_data(document, number_of_query, keyword_list)

        # Re-factory index_data to be a unique set of content data
        unique_page_content = set(data['content'] for data in index_data)
        new_list = [next(data for data in index_data if data['content'] == page_content) for page_content in unique_page_content]
        new_list.sort(key=lambda data: index_data.index(data))

        # Get data content from the unique data list
        retrieved_data = [data['content'] for data in new_list]
        # Get metadata from the unique data list
        metadatas = [data['metadata'] for data in new_list]

        # Handle metadata to obtain neccessary information
        reference_links, wkproduct_links, guideline_links, guidelines = self.obtainMetadata(metadatas)

        # Handle Acronyms
        acronyms = []
        for link in reference_links:
            if 'AUTOSAR' in link:
                if ':' in link:
                    # # Step 1: Find the index of the first backslash
                    # start_index = link.find('\\') + 1

                    # # Step 2: Find the index of the dot, then find the last backslash before it
                    # dot_index = link.find('.')
                    # end_index = link.rfind('\\', 0, dot_index)

                    # Step 1: Find the index of the first backslash
                    start_index = link.find('\\') + 1

                    # Step 2: Find the index of the dot, then find the last backslash before it
                    end_index = link.find('|')
                    # Extract the substring
                    link = link[start_index:end_index]

                    folder_link = config.data + 'internal/' + ('/').join(link.split('\\')[:2])
                    document_name = link.split('\\')[-1].split('.')[0]

                else:
                    folder_link = config.data + 'internal/' + ('/').join(link.split('/')[:2])
                    document_name = link.split('/')[-1].split('.')[0]

                with open(folder_link + '/data.json', 'r') as file:
                    json_data = json.load(file)
                    for part in json_data['acronym'][document_name]:
                        acronyms.append(part)
        unique_acronyms = []
        existing_names = set()
        for acronym in acronyms:
            if acronym["name"] not in existing_names:
                unique_acronyms.append(acronym)
                existing_names.add(acronym["name"])
        for i in range(len(retrieved_data)):
            for acronym in unique_acronyms:
                if acronym['name'] in retrieved_data[i]:
                    retrieved_data[i] += '\n'
                    retrieved_data[i] += acronym['name'] + ' stand for ' + acronym['description']

        return retrieved_data, reference_links, wkproduct_links, guideline_links, guidelines