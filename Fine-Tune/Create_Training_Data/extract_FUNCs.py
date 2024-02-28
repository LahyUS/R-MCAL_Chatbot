import os
import re

# Function to extract function definitions from a C source file
def extract_function_definitions(file_path):
    with open(file_path, 'r') as file:
        content = file.read()

        # Pattern to match the start of each function definition
        pattern = r"\s*\*\*\s+Function\s+Name\s+[\s\S]*?{"

        # Extract function definitions using regex
        function_definitions = re.finditer(pattern, content)
        definitions = []
        for match in function_definitions:
            function_start = match.start()
            opening_brace_count = 0
            closing_brace_count = 0
            i = function_start
            while i < len(content):
                if content[i] == '{':
                    opening_brace_count += 1
                elif content[i] == '}':
                    closing_brace_count += 1
                if opening_brace_count > 0 and opening_brace_count == closing_brace_count:
                    definitions.append(content[function_start:i + 1])
                    break
                i += 1

        return definitions


def extract_function_definitions_from_directory(directory):
    parent_directory = os.path.dirname(os.path.normpath(directory))
    output_directory = os.path.join(parent_directory, "function_definitions")
    os.makedirs(output_directory, exist_ok=True)
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".c"):
                file_path = os.path.join(root, file)
                function_definitions = extract_function_definitions(file_path)

                for idx, func_def in enumerate(function_definitions, start=1):
                    function_name_match = re.search(r"\*\* Function Name\s*:\s*([A-Za-z0-9_]+)", func_def)
                    if function_name_match:
                        function_name = function_name_match.group(1)
                        output_file_path = os.path.join(output_directory, f"{function_name}.txt")
                        with open(output_file_path, 'w') as output_file:
                            output_file.write(func_def)


# Path to the directory containing C source files
directory_path = "path/to/your/source/code"
input_folder = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/MCAL_func_defs/external/rel/modules/'
output_folder = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/JSON_Test_Spec'

# Path to the directory containing module folders
modules_directory = 'C:/Users/rvc_sw_mss1_common/Desktop/Create_Training_Data/MCAL_func_defs/external/rel/modules/'

# Iterate through module directories
for module in os.listdir(modules_directory):
    module_path = os.path.join(modules_directory, module)
    if os.path.isdir(module_path):
        src_directory = os.path.join(module_path, "src")
        if os.path.exists(src_directory) and os.path.isdir(src_directory):
            extract_function_definitions_from_directory(src_directory)