import time
import warnings
import re

print(f"\n########### INITIALIZATION PHASE ###########")
start_time = time.time()
from _tokenizer import TOKENIZER
from _keyword import KEYWORD
from _retrieve import RETRIEVE
from _database import DATABASE
from _classifyQuestion import CLASSIFY_QUESTION
from _correctSpelling import CORRECT_SPELLING
end_time = time.time()
processing_time = end_time - start_time
print(f"\nTOTAL INTIALIZATION TIME: {processing_time}\n\n")

from _utils import *
from _config import CONFIG
from _const_define import *

config = CONFIG()

class QnA:
    def __init__(self):
        start_time_qa = time.time()

        self.Keyword = KEYWORD()
        self.Retrieve = RETRIEVE()
        self.Tokenizer = TOKENIZER()
        self.Database = DATABASE()
        self.ClassifyQuestion = CLASSIFY_QUESTION()
        self.CorrectSpelling = CORRECT_SPELLING()
        self.previous_retrieved_data = []
        self.previous_reference = []

        end_time_qa = time.time()
        QA_init_time = end_time_qa - start_time_qa
        print(f"\nQA_init_time: {QA_init_time} seconds")


    def get_query_data(self, path, question):
        """
        This function is used to get retrieved data and reference (link to document). Including:
        + Get keywords from question
        + Retrieve data and reference based on folder path and question keywords
        """
        self.query = self.Keyword.get_key_query(question)
        self.retrieved_data, self.reference = self.Retrieve.run(path,self.query, config.number_of_query)
        return self.query, self.retrieved_data, self.reference


    def get_query_data_with_classify_question(self, path, question):
        """
        This function is used to get retrieved data and reference (link to document). Including:
        + Get keywords from question
        + Classify question to know if it is follow up question, from that we can get relevant ratio of previous and new retrieved data/reference
        + Retrieve data and reference based on folder path and question keywords
        + Combine previous and new retrieved data/reference to get final retrieved data/reference
        """
        # Extract keywords from the raw question
        # query = self.Keyword.get_key_query(question)
        # Classify question for more accurate prompt
        index_type, nouns, prop_nouns = self.ClassifyQuestion.run(question)
        # Convert sets to lists and concatenate the words with a space as the separator
        query = ' '.join(list(nouns) + list(prop_nouns))

        if index_type == CLASSIFY_GREET_SENTENCE:
            return question, "", "", [], [], [], NONCHAINCONVERSATION

        elif index_type == CLASSIFY_MOST_RELATED or index_type == CLASSIFY_MEDIUM_RELATED:
            return question, "", "", [], [], [], CHAINCONVERSATION

        else:
            # Retrieve new data and references with the expected ratio 
            retrieved_data, references, new_wkproduct_links, guideline_links, guidelines = self.Retrieve.run(path, query, int(config.number_of_query))

            references = references[:min(config.link_number, len(references))] # Limit the reference list

            return query, retrieved_data, references, new_wkproduct_links, guideline_links, guidelines, NONCHAINCONVERSATION

    def generate_prompt(self, path, question, common_prompt, specific_prompt, history):
        """This function is used to generate prompt from given path, question, prompt and history. Including:
        + Retrieve data based on path and question
        + Reduce the number of retrieved data if token_length > max_token
        + Create final prompt
        """
        #if config.correct_spelling:
            #question = self.CorrectSpelling.run(question)
            
        # We can choose to use get_query_data or get_query_data_with_classify_question function
        query, retrieved_data, references, wkproduct_links, guideline_links, guidelines, conversation_type = self.get_query_data_with_classify_question(path, question)
        
        # Remove the references if they are not related to AUTOSAR
        if any('autosar' not in ref.lower() or 'hardwaremanual' in ref.lower() for ref in references):
            references = ""

        to_be_used_prompt = "" 
        if len(retrieved_data) == 0: 
            to_be_used_prompt = common_prompt
            prompt_type = 1
        else:
            to_be_used_prompt = specific_prompt
            prompt_type = 2

        history_conversation = ''
        # If history has already existed, then replace it into the prompt
        if len(history) > 0: 
            for data in history:
                history_conversation += '### Instruction: ' + data[0] + '\n'
                history_conversation += '### Response: ' + data[1] + '\n'
            middle_prompt = to_be_used_prompt.replace('{history}', history_conversation.rstrip('\n'))
        else: 
            # Remove history part in the prompt
            if prompt_type == 1:
                middle_prompt = to_be_used_prompt.replace('History: {history}', '') 
            else: 
                middle_prompt = to_be_used_prompt.replace('{history}', '')

        # Replace question into the prompt
        middle_prompt = middle_prompt.replace('{question}', question) 
        
        # If there is no retrieved data, immediately return the middle prompt
        if len(retrieved_data) == 0: 
            print('Warning: no data retrieved')
            # Remove history part in the prompt
            if prompt_type == 1:
                middle_prompt = middle_prompt.replace('Information: {input}', '')
            else: 
                middle_prompt = middle_prompt.replace('{input}', '')

            middle_prompt = '###' + middle_prompt.split('###', 1)[1]
            # Use a regular expression to remove consecutive empty lines
            middle_prompt = re.sub(r'\n\s*\n', '\n', middle_prompt)
            return middle_prompt, references, [], [], [], conversation_type

        token_length = config.max_token
        data_length = len(retrieved_data) + 1
        input = ''
        while(token_length >= config.max_token):
            data_length -= 1
            if data_length == 0:
                print('Warning: exceed max token -> can not retrieve any data')
                final_prompt = middle_prompt.replace('{input}', '')
                break

            input = ''
            # Iterate through the retrieved data list
            for i in range(data_length): 
                # Add header for each piece of information sentence
                input += 'information ' + str(i+1) + ':\n' 
                # Add the content body of the current information sentence
                input += retrieved_data[i] 
                # Add footer of the current information sentence
                input += '\nend of information ' + str(i+1) + '\n' 

            final_prompt = middle_prompt.replace('{input}', input) # Insert the formatted retrieved data into the final prompt
            token_length = self.Tokenizer.tokenizer(final_prompt, return_tensors='pt').input_ids.size(1)

        return final_prompt, references, wkproduct_links, guideline_links, guidelines, conversation_type
    

    def generate_related_question_prompt(self, question, prompt, history = []):
        """
        This function is used to ask the model to generate related question for current question-answer
        """
        history_conversation = ''
        for data in history:
            history_conversation += '### Instruction: ' + data[0] + '\n'
            history_conversation += '### Response: ' + data[1] + '\n'
        final_prompt = prompt
        final_prompt = final_prompt.replace('{question}', question)

        return final_prompt
    

    def save_external_files(self, json_data, document_path, document_name):
        """
        # This function is used in External file chat feature. Including:
        # + Receive json_data from web ui and save to final database as conversation id
        # + Use when user upload new External file to web ui
        """
        self.Database.save_external_files(json_data, document_path, document_name)


    def delete_external_files(self, document_path):
        """
        This function is used in External file chat feature. Including:
        # + Remove folder based on conversation id when user delete conversation
        """
        self.Database.delete_external_files(document_path)

