##########################################################################################################
# Test Show Dictionary
##########################################################################################################
import sys
from _correctSpelling import CORRECT_SPELLING

def log_dict(log_file):
    # Redirect stdout to the log file
    original_stdout = sys.stdout
    with open(log_file, "w", encoding="utf-8") as log_file:
        sys.stdout = log_file

        grammar = CORRECT_SPELLING()
        #grammar.preprocess_dictionary(grammar.sym_spell._words)
        vocabs = grammar.sym_spell
        more_requens = {}
        for word, count in vocabs._words.items():
            if count >= 2:
                more_requens[word] = count

        for word, count in vocabs._words.items():
            print(word, ' - ', count)

    # Redirect stdout to the log file
    original_stdout = sys.stdout

##########################################################################################################
# Test Updata Dictionary
##########################################################################################################
# import sys
# from _correctSpelling import CORRECT_SPELLING
# new_json_data = "../02_Final_Data/final_data_v5/internal/MCAL_WPS/data.json"
# save_file_path = "../model/sym_spell_v2.pkl"
# grammar = CORRECT_SPELLING()
# grammar.update_dict_with_new_data(new_json_data, save_file_path)

new_json_data = "../02_Final_Data/final_data_v5/internal/MCAL_WPS/data.json"
save_file_path = "../model/sym_spell_v2.pkl"
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python download_models.py command [arguments...]")
        print("Available mode: update, log")
        sys.exit(1)

    mode = sys.argv[1]
    if mode == "update":
        print("Update mode")
        if len(sys.argv) == 4:
            new_json_data = sys.argv[2]
            save_file_path = sys.argv[3]
        print(f"new_json_data: {new_json_data}")
        print(f"save_file_path: {save_file_path}")
        grammar = CORRECT_SPELLING()
        grammar.update_dict_with_new_data(new_json_data, save_file_path)

    elif mode == "log":
        print("Log mode")
        if len(sys.argv) == 3:
            log_path = sys.argv[2]
        log_path = "dict_v3.txt"    
        print(f"log_path: {log_path}")
        log_dict(log_path)
    
    else:
        print("Usage: python download_models.py command [arguments...]")
        print("Available mode: update, log")