from KeyBERT.keybert import KeyBERT
from sklearn.feature_extraction.text import CountVectorizer
import warnings
import nltk
from _utils import *
import yaml
from _config import CONFIG
import re

config = CONFIG()

class KEYWORD:
    def __init__(self, n_gram_range = (1, 2), top_n = 1, stop_words = "english"):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            '''
            The CountVectorizer class implements the process of tokenizing the text, building a vocabulary of known words, 
            and encoding each document as a vector of word counts. It represents a bag-of-words model, 
            where each document is treated as an unordered collection of words, disregarding grammar and word order.
            '''
            self.vectorizer = CountVectorizer(ngram_range=n_gram_range, stop_words=stop_words, tokenizer=self.custom_tokenizer, min_df=1)
            self.kw_model = KeyBERT(model=config.embedding_dir)
            self.related_to_prev_sentence_phrase  = { "keep going",
                "continue", "persist", "carry on", "press on", "keep on", "go on", "move forward",
                "never give up", "stick with it", "forge ahead", "stay the course", "persevere",
                "hold on", "maintain momentum", "keep at it", "don't stop", "soldier on",
                "keep the faith", "endure", "stay persistent", "go ahead"
            }
        self.top_n = top_n
        
    def custom_tokenizer(self, text:str):
        token = text.split()
        return token
    
    def get_keywords(self, text:str):
        text = text.replace('?','')
        final_keywords = ''
        try:
            keywords = self.kw_model.extract_keywords(text,
                                                      keyphrase_ngram_range=(1, 2),  # Extract unigrams and bigrams
                                                      vectorizer = self.vectorizer,
                                                      use_mmr=True, 
                                                      diversity=0.7,
                                                      highlight=True, 
                                                      top_n=self.top_n)                                                    
        except:
            return ''

        final_keywords = keywords[0][0]
        #if config.debug:
            #print('Keywords:',final_keywords)

        return final_keywords

    def check_for_most_related_query(self, query:str):
        lower_sentence = query.lower()
        for phrase in self.related_to_prev_sentence_phrase:
            if phrase in lower_sentence:
                return phrase
        return ''

    def get_key_query(self, query:str):
        """Utilize keyBERT to extract keywords from the given query. 
        \n\tThen generate a key query that could be more helpful for data retrieving.
        """

        # Get keywords from the give query
        keywords = self.get_keywords(query) 
        # Find words in a sentence where all characters are uppercase. Ex: CAN, LIN, ADAS
        uppercase_words = re.findall(r'\b[A-Z]+\b', query)

        if keywords == '' and uppercase_words == '':
            print('Warning: no keywords found')
            return ''

        # Post-Process the keyquery
        keywords = keywords.split() # Split whitespace characters
        words = query.replace('?','').split() # Split whitespace characters
        key_query = [word for word in words if convertLowerCase(word) in keywords]
        key_query = (' ').join(key_query) 
        key_query = (' ').join(uppercase_words) 

        for word in words:
            # Tokenize a text string into individual words or tokens. 
            tokens = nltk.word_tokenize(convertLowerCase(word)) 
            # Assign a grammatical category (part-of-speech) to each word in a given text.
            pos_tag = nltk.pos_tag(tokens) 
            if  pos_tag[0][1] == 'PRP' and pos_tag[0][0] not in ["I", "you", "we"]: # Keep prp like they, he, she, it,
                key_query += ' ' + word

        return key_query
        
