import os
import re
import json
import random
import re

def extract_code_after_reference_id(input_string):
    # Define a regex pattern to match everything after the last occurrence of '** Reference ID'
    pattern = re.compile(r'\*\* Reference ID\s*:\s*(.*?)\n', re.DOTALL)
    
    # Find all matches
    matches = pattern.findall(input_string)
    
    if matches:
        # Get the last match and return the portion of the string after it
        last_match = matches[-1]
        index = input_string.find(last_match) + len(last_match)
        return input_string[index:].strip()
    else:
        # If no match is found, return the original string
        return input_string

def clean_texts(input_string):
    cleanned_string = re.sub(r'\*{3,}', '', input_string)
    #cleanned_string = re.sub(r'\*\* Reference ID\s*:\s*.*', '', cleanned_string)
    cleanned_string = re.sub(r'\s+', ' ', cleanned_string)
    
    return cleanned_string

# Function to extract function definitions from a C source file
def extract_test_case_from_json(train_output_file_path):
    with open(train_output_file_path, 'r') as file:
        content = json.load(file)
        return content

def convert_variable(input_var, is_input):
    if is_input:
        # Convert dictionary to string representation
        str_representation = str(input_var)
        str_representation = extract_code_after_reference_id(str_representation)
        str_representation = clean_texts(str_representation)
          

    else:
        # Convert dictionary to string representation
        str_representation = str(input_var)
        
        # Replace braces with square brackets
        str_representation = str_representation.replace('{', '[').replace('}', ']')

    return str_representation

def create_training_data_from(module, train_input_dir, train_output_dir, train_data_directory):
    train_output_directory = os.path.join(train_data_directory, module)
    os.makedirs(train_output_directory, exist_ok=True)
    for train_input_root, dirs, train_input_files in os.walk(train_input_dir):
        for train_input_file in train_input_files:
            if train_input_file.endswith(".txt"):
                train_input_file_path = os.path.join(train_input_root, train_input_file)
                input_data_part = ""
                output_data_part = ""

                with open(train_input_file_path, 'r') as file:
                    input_data_part = file.read()
                    
                function_name = train_input_file.split('.')[0]
                train_output_file_path = os.path.join(train_output_dir, module, function_name + ".json")
                if os.path.exists(train_output_file_path):
                    output_data_parts = extract_test_case_from_json(train_output_file_path)

                    for idx, test_case in output_data_parts.items():
                        final_output_file_path = os.path.join(train_output_directory, f"{function_name}.json")
                        expected_test_case = convert_variable(test_case, is_input=False)
                        expected_input = convert_variable(input_data_part, is_input=True)
                        completed_train_item = {"Input": expected_input, 
                                                "Output": expected_test_case}
                        json_string = json.dumps(completed_train_item)
                        with open(final_output_file_path, 'a') as output_file:
                            output_file.write(json_string + "\n")


def create_final_training_data(module_path, FINAL_DATA_FILE_PATH):
    for train_input_root, dirs, train_input_files in os.walk(module_path):
        for train_input_file in train_input_files:
            if train_input_file.endswith(".json"):
                train_input_file_path = os.path.join(train_input_root, train_input_file)

                with open(train_input_file_path, 'r') as file:
                    for line in file:
                        json_object = json.loads(line)
                        json_string = json.dumps(json_object)
                        
                        with open(FINAL_DATA_FILE_PATH, 'a') as output_file:
                            output_file.write(json_string + "\n")


# Function to split items into train and validation datasets
def split_jsonl(input_file, train_file, validation_file, train_ratio):
    with open(input_file, 'r') as input_data, open(train_file, 'w') as train_data, open(validation_file, 'w') as validation_data:
        for line in input_data:
            # Read each line (JSON object) from the input file
            json_object = json.loads(line)

            # Decide whether to write to train or validation file based on the ratio
            if random.random() < train_ratio:
                # Write to train file
                train_data.write(json.dumps(json_object) + '\n')
            else:
                # Write to validation file
                validation_data.write(json.dumps(json_object) + '\n')


# Path to the directory containing C source files
directory_path = "path/to/your/source/code"
input_folder = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/MCAL_func_defs/external/rel/modules/'
output_folder = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/JSON_Test_Spec'

# Path to the directory containing module folders
input_modules_directory = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/MCAL_func_defs/external/rel/modules/'
output_modules_directory = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/JSON_Test_Spec'
train_data_directory = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/Training_Data'

raw_train_data = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/Training_Data/FINAL_DATA/train.jsonl'
train_output = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/Training_Data/FINAL_DATA/final_train.jsonl'
validation_output = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/Training_Data/FINAL_DATA/final_validation.jsonl'

os.makedirs(train_data_directory, exist_ok=True)

# How to use this script: Set True value one by one for the macros:
CREATE_PRE_DATA = True        # 1
CREATE_FINAL_DATA = True      # 2
SPLIT_TRAIN_VALID_DATA = True # 3

if __name__ == "__main__":
    if CREATE_PRE_DATA:
        # Iterate through module directories
        for module in os.listdir(input_modules_directory):
            module_path = os.path.join(input_modules_directory, module)
            if os.path.isdir(module_path):
                func_def_directory = os.path.join(module_path, "function_definitions")
                if os.path.exists(func_def_directory) and os.path.isdir(func_def_directory):
                    create_training_data_from(module, func_def_directory, output_modules_directory, train_data_directory)

    if CREATE_FINAL_DATA:
        FINAL_DATA_DIR = os.path.join(train_data_directory, "FINAL_DATA")
        FINAL_DATA_FILE_PATH = os.path.join(FINAL_DATA_DIR, "train.jsonl")
        os.makedirs(FINAL_DATA_DIR, exist_ok=True)

        # Iterate through module directories
        for module in os.listdir(train_data_directory):
            module_path = os.path.join(train_data_directory, module)
            if os.path.isdir(module_path) and module != "FINAL_DATA":
                create_final_training_data(module_path, FINAL_DATA_FILE_PATH)

    if SPLIT_TRAIN_VALID_DATA:
        # Split the items from input_jsonl file into train and validation datasets (with a 9:1 ratio)
        split_jsonl(raw_train_data, train_output, validation_output, 0.97)