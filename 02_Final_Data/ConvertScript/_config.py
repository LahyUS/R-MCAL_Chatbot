import yaml
from extern_variables import *

class CONFIG:
    def __init__(self):
        # with open('/home/banvien/PROJECT/Work/Chatbot/code/Create_final_data/version_4/config.yaml', 'r') as file:
        config_file_path = CONFIG_PATH
        with open(config_file_path, 'r') as file:
            config = yaml.safe_load(file)

            self.debug = config['debug']
            self.middle_version_path = config['middle_version_path']
            self.key_path = config['key_path']
            self.tokenizer_path = config['tokenizer_path']
            self.embedding_dir = config['embedding_dir']