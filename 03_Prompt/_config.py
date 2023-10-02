import yaml

class CONFIG:
    def __init__(self):
        config_file_path = '/content/drive/MyDrive/Colab_env/Chatbot/code/MCAL_BOT/config.yaml'
        # config_file_path = './config.yaml'
        with open(config_file_path, 'r') as file:
            config = yaml.safe_load(file)
            self.environment = config['environment']
            self.root = ''
            if self.environment == 'colab':
                self.root = config['root_colab']
            elif self.environment == 'local':
                self.root = config['root_local']

            self.key_path = self.root + config['key_path']
            self.data = self.root + config['data']
            self.sym_spell_dict = self.root + config['sym_spell_dict']
            if self.environment == 'colab':
                self.embedding_dir = config['embedding_model']
                self.model_dir = config['LLM_model']
            elif self.environment == 'local':
                self.embedding_dir = self.root + config['embedding_model']
                self.model_dir = self.root + config['LLM_model']

            self.correct_spelling = config['correct_spelling']
            self.need_decode = config['need_decode']
            self.max_token = config['max_token']
            self.retriever = config['retriever']
            self.threshold = config['threshold']
            self.number_of_query = config['number_of_query']
            self.link_number = config['link_number']
            self.debug = config['debug']