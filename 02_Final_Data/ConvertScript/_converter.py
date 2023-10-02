import os

import glob
from _loader import *
from _saver import *
from _textSplitter import MyTextSplitterr
from _utils import *
from _config import CONFIG
config = CONFIG()

# Turn off warning log of transformer library
import logging
logging.getLogger("transformers").setLevel(logging.ERROR)

class CONVERTER():
    def __init__(self, type):
        self.Loader = LOADER(type)
        self.type = type

    def child_folder(self, path):
        # Get the list of .json file
        json_file_paths = glob.glob(path + "/*.json")

        if len(json_file_paths) > 0:
            # Create error log file
            save_path = path.replace(config.middle_version_path, self.internal_path)
            error_log_path = f'{save_path}/{os.path.basename(save_path)}.txt'
            with open(error_log_path, 'w') as file:
                file.write('This is error log of ' + path + '\n')

            if config.debug:
                print('Create final data from', path.replace(f'{config.middle_version_path}/',''))
                print('+++ Getting documents:')
            
            # Load all .json file in the list
            docs = self.Loader.multipleFilesLoad(json_file_paths, self.type, error_log_path)

            if config.debug:
                print('+++ Number of documents before split:', len(docs))
                print('+++ Documents splitting in progress:')

            # Split the loaded content into small chunks
            text_splitter = MyTextSplitterr(separator = '\n', chunk_size = 500)
            docs = text_splitter.split_documents(docs)

            if config.debug:
                print('+++ Number of documents after split:', len(docs))

            # Save document into file
            self.Saver.save(docs, save_path)

            if self.type == 'AUTOSAR':
                converTool = AUTOSAR()
                print('+++ Get acronyms and abbreviations:')
                converTool.AcronymsAndAbbreviations(json_file_paths, self.type, f'{save_path}/data.json')

            if config.debug:
                print()

        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path):
                self.child_folder(item_path)                    

    def run(self, module_sub_path, output_path, save_format, encode):
        # Create external and internal folder
        external_path = os.path.join(output_path,'external')
        os.makedirs(external_path, exist_ok=True)
        self.internal_path = os.path.join(output_path,'internal')
        os.makedirs(self.internal_path, exist_ok=True)

        # Create output folder to be similar with input
        replicate_folder_structure(config.middle_version_path, self.internal_path)

        self.save_format = save_format
        self.Saver = SAVER(self.save_format, self.type, encode)
        middle_data_path = os.path.join(config.middle_version_path, module_sub_path)
        self.child_folder(middle_data_path)
