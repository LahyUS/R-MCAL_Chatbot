import spacy
from _utils import *
from _const_define import *
import re

class CLASSIFY_QUESTION:
    def __init__(self):
        '''
        Load the English language model provided by spacy.
        The model contains pre-trained word vectors and linguistic annotations.
        '''
        self.nlp = spacy.load("en_core_web_lg")
        self.unaccepted_pronouns = ['who', 'whom', 'whose', 'which', 'what', 'me', 'I', 'you', ]
        self.greeting_words = ['hello', 'yo' , 'hey' ,'hi', 'hmm', 'holy', 'oh', 'wow', 'oops', 'ah', 'haha', 'great', 'aw', 'haizz']
        # Check for verb phrases in the sentence
        self.verb_phrases = {'tell', 'explain', 'show', 'describe', 'introduce', 'teach', 'discuss',
                        'elaborate', 'mention', 'talk about', 'provide details on', 'clarify',
                        'illustrate', 'provide information about', 'share insights on',
                        'shed light on', 'offer an explanation for', 'go over'}
        
    def run(self, question):
        if not question.strip():
            return CLASSIFY_GREET_SENTENCE  # Handle empty input

        # The self.nlp object applies linguistic annotations and analyzes the question, producing a Doc object that represents the processed text.
        doc = self.nlp(question) 
        has_verb_phrase = any(phrase in doc.text.lower() for phrase in self.verb_phrases)

        pronouns = {token.text for token in doc if token.pos_ == 'PRON' and convertLowerCase(token.text) not in self.unaccepted_pronouns}
        nouns = {token.text for token in doc if token.pos_ == 'NOUN'}
        # Proper nouns are typically capitalized and refer to specific entities rather than general concepts.
        uppercase_words = re.findall(r'\b[A-Z]+\b', question)
        proper_nouns = {token.text for token in doc if token.pos_ == 'PROPN' or (token.text in uppercase_words)}
        interjections = {token.text for token in doc if token.pos_ == 'INTJ' or token.pos_ == 'ADJ' or token.pos_ == 'VERB' or token.lower_ in self.greeting_words}

        # Get Named Entities
        named_entities = {ent.text: ent.label_ for ent in doc.ents}

        index_type = (
        # CLASSIFY_LITTLE_RELATED Ex: Tell me about ADC_init; Introcude me about US;
        CLASSIFY_LITTLE_RELATED if (has_verb_phrase and (len(nouns) + len(proper_nouns)) > 0) or (len(nouns) + len(proper_nouns)) > 0 and len(pronouns) == 0 else# and len(interjections) == 0: 
        CLASSIFY_MEDIUM_RELATED if (len(nouns) + len(proper_nouns)) > 0 and len(pronouns) > 0 else # Ex: Do ADC_Init relate to it
        CLASSIFY_MOST_RELATED   if (len(nouns) + len(proper_nouns)) == 0  and has_verb_phrase and len(pronouns) > 0 else # Ex: Explain about it
        CLASSIFY_MOST_RELATED   if (len(pronouns) > 0) and (len(proper_nouns) + len(nouns) == 0) else
        CLASSIFY_GREET_SENTENCE if  len(pronouns) + len(interjections) > 0 else # Ex: Hi guy; It is amazing
        CLASSIFY_GREET_SENTENCE
        )
        return index_type, nouns, proper_nouns