import json
import pickle
from _utils import *
from symspellpy import SymSpell, Verbosity
from _config import CONFIG
from collections import Counter
config = CONFIG()
import time

class CORRECT_SPELLING:
    def __init__(self):
        if config.correct_spelling:
            try:
                if config.debug:
                    print('Loading correct spelling dictionary ...')
                    print(config.sym_spell_dict)
                with open(config.sym_spell_dict, 'rb') as f:
                    self.sym_spell = pickle.load(f)
            except:
                print('Error: Can not load sym spell dictionary')
        self.greeting_words = ('hello', 'hi', 'hmm', 'holy', 'oh', 'wow', 'oops', 'ah', 'haha', 'great', 'aw')
        
        self.stop_words = (
                    "a", "about", "above", "after", "again", "against", "all", "am", "an",
                    "and", "any", "are", "aren't", "as", "at", "be", "because", "been",
                    "before", "being", "below", "between", "both", "but", "by", "can't",
                    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't",
                    "doing", "don't", "down", "during", "each", "few", "for", "from", "further",
                    "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", "he'd",
                    "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself",
                    "his", "how", "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into",
                    "is", "isn't", "it", "it's", "its", "itself", "let's", "me", "more", "most",
                    "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
                    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over",
                    "own", "same", "shan't", "she", "she'd", "she'll", "she's", "should",
                    "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their",
                    "theirs", "them", "themselves", "then", "there", "there's", "these", "they",
                    "they'd", "they'll", "they're", "they've", "this", "those", "through", "to",
                    "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll",
                    "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", "where",
                    "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with",
                    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've",
                    "your", "yours", "yourself", "yourselves"
                )
    
    def run(self, text):
        words = text.split(' ')
        # simplified_words = [self.preprocess_word(word) if word not in self.stop_words else word for word in words]
        """
        The three available verbosity levels are:
            + Verbosity.TOP:     Returns only the top suggestion with the highest probability. This is the fastest option.
            + Verbosity.CLOSEST: Returns suggestions with the shortest edit distance to the input word. This is often the most accurate option.
            + Verbosity.ALL:     Returns all suggestions within the max_edit_distance limit, sorted by edit distance.

        Typically, max_edit_distance values range from 1 to 3, where:
            + 1: allows for corrections with a single-character edit (insertion, deletion, or substitution).
            + 2: allows for corrections with up to two-character edits.
            + 3: allows for corrections with up to three-character edits.
        """
        simplified_words = []
        for word in words:
            simplified_word = self.preprocess_word(word)
            # Skip the correct spelling for the most common words
            if simplified_word is None or word in self.stop_words or word.lower() in self.greeting_words:
                simplified_words.append(word)
            # Handle the simplified word and correct it if there is a grammatical systax error
            else:
                correction = self.sym_spell.lookup(simplified_word, Verbosity.CLOSEST, max_edit_distance=1, include_unknown=True)
                if correction:
                    simplified_words.append(correction[0].term)
                else:
                    simplified_words.append(word)
        
        # If all the words are None, it means this is a common sentence, just return
        if all(element is None for element in simplified_words):
            return ' '.join(words)

        return ' '.join(filter(None, simplified_words))

    def create_word_frequency_dict(self, word_list):
        word_count = Counter(word_list)
        return word_count

    def update_dict(self, source_dict, target_dict):
        for word, frequency in source_dict.items():
            if word in target_dict:
                target_dict[word] += frequency
            else:
                target_dict[word] = frequency

    def getsplitterwords(self, json_file_path):
        try:
            with open(json_file_path, "r") as json_file:
                json_data = json.load(json_file)
                
            splitter_words = []

            for entry in json_data["document"]:
                content = entry.get("content", "")
                words = content.split()
                
                # Remove stop words, numbers, and single characters
                preprocessed_words = [self.preprocess_word(word) for word in words]
                valid_words = [word for word in preprocessed_words if word is not None]
                splitter_words.extend(valid_words)
            
            return splitter_words
        except Exception as e:
            print(f"An error occurred: {e}")
            return []

    def preprocess_word(self, word):
        # Regular expression pattern for characters to replace
        pattern = r"[*\n-\"'{}()]"  # Add more characters if needed
        
        # Regular expression pattern to remove number.phrase format
        number_phrase_pattern = r"\d+[._]\w+"  # Matches patterns like 2.ABC or 03_RD
        # Additional pattern to remove numbers with commas (e.g., 1,5)
        number_comma_pattern = r"\d+(?:,\d+)+"
        # Regular expression pattern for common file name formats
        file_name_pattern = r"\.(o|c|h|cpp|log|yaml|pkl|sh|bat|txt|py|java)$"

        

        if word == "03_RD":
            print(word)

        # Check if the word contains at least one character from a-z or A-Z
        if not any(char.isalpha() for char in word):
            return None

        # Check if the word is an URL
        elif re.match(r"https?://\S+", word) or re.match(r"http?://\S+", word):
            return None  # Return the original word (URL) as-is

        # Check if the word matches the file name pattern
        elif re.search(file_name_pattern, word.lower()):
            #print(f"filename: {word}")
            parts = word.split('.')
            if len(parts) > 2:
                main_filename = ".".join(parts[:-1])
                extension = parts[-1]
                main_filename = re.sub(r"[^\w\s]", "", main_filename)
                print(f"{main_filename}.{extension}")
                return f"{main_filename}.{extension}"

            elif len(parts) == 2:
                filename, extension = parts
                filename = re.sub(r"[^\w\s]", "", filename)
                print(f"{filename}.{extension}")
                return f"{filename}.{extension}"  # Return file names without further processing

        # Handle colon in the word
        elif ":" in word:
            if word.startswith(":") or word.endswith(":"):
                word = re.sub(r"[^\w\s]", "", word)  # Remove punctuation
                return re.sub(r'^:|:$', '', word)
            else:
                word = re.sub(r"[^\w\s:]", "", word)  # Remove unnecessary characters
                return word.replace(":", "-")

        elif "-" in word:
            # Remove hyphens at the beginning or end of a word
            word = re.sub(r'^-', '', word)
            word = re.sub(r'-$', '', word)
            # Apply preprocessing steps
            word = re.sub(pattern, " ", word)
            word = re.sub(number_phrase_pattern, "", word)
            word = re.sub(number_comma_pattern, "", word)
            word = re.sub(r"[^a-zA-Z0-9\s_-]", "", word)  # Remove non-alphanumeric characters
        
        else:
            # Apply preprocessing steps
            word = re.sub(pattern, " ", word)
            word = re.sub(number_phrase_pattern, "", word)
            word = re.sub(number_comma_pattern, "", word)
            word = re.sub(r"[^\w\s]", "", word)  # Remove punctuation
            word = re.sub(r"[^a-zA-Z0-9\s_]", "", word)  # Remove non-alphanumeric characters
        
        # Remove stop words, numbers, and single characters
        if (
            word.lower() not in self.stop_words and
            not word.isdigit() and
            len(word) > 1
        ):
            return word
        else:
            return None  # Return None for words to be filtered out

    def preprocess_dictionary(self, word_dict):
        words_to_remove = []

        # Create a list of keys to iterate over
        words_to_check = list(word_dict.keys())

        for word in words_to_check:
            frequency = word_dict[word]
            updated_word = self.preprocess_word(word)
            if updated_word == None:
                words_to_remove.append(word)
            elif updated_word != word:
                words_to_remove.append(word)
                word_dict[updated_word] = frequency

        # Remove the old words
        for word in words_to_remove:
            del word_dict[word]

    def update_dict_with_new_data(self, json_file_path, save_file_path):
        self.preprocess_dictionary(self.sym_spell._words)
        old_data = list(self.sym_spell._words.keys())
        new_data = self.getsplitterwords(json_file_path)
        new_dict = self.create_word_frequency_dict(new_data)
        self.update_dict(self.sym_spell._words, new_dict)
        #concat_data = old_data + new_data
        self.create_dict(new_dict, save_file_path)

    def create_dict(self, word_dict, save_path):
        # word_list = list(set(word_list))
        # word_count = {}
        # for word in word_list:
        #     if word in word_count:
        #         word_count[word] += 1
        #     else:
        #         word_count[word] = 1

        word_list_with_count = [(word, count) for word, count in word_dict.items()]
        sym_spell = SymSpell(max_dictionary_edit_distance=2, prefix_length=40)

        for word, count in word_list_with_count:
            sym_spell.create_dictionary_entry(word, count)

        with open(save_path, 'wb') as f:
            pickle.dump(sym_spell, f)
