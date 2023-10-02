<!-- GETTING STARTED -->
## Getting Started

### Create Virtual Environment
```sh
python -m venv ./venv
cd venv
cd Scripts
activate
python -m pip install --upgrade pip
```

### Install Packages & Dependencies
#### Install packages
```sh
pip install -r requirements.txt
```

#### Install Dependencies
##### Model
Need to download 2 huggingface models to folder '../model' (code in MCAL_BOT/basic_usage.py)
* gpt4-x-vicuna-13B-GPTQ
* all-mpnet-base-v2-table
```sh
python install_dependencies.py install_models ./model TheBloke/gpt4-x-vicuna-13B-GPTQ deepset/all-mpnet-base-v2-table
```
* NLTK Vocabularies
```sh
python install_dependencies.py install_nltk_data punkt averaged_perceptron_tagger wordnet stopwords
```

##### Spacy library:
```sh
python -m spacy download en_core_web_lg
python -m spacy download en_core_web_sm
```

## Usage
### Configuration
The system should be run on 2 environments: GG Colab or Local PC.
1. Open config.yaml
2. Comment & Uncomment configure such that it suitable for the system.

### Modify config.yaml for config module could access
1. Open _config.py
2.  In line 5, change the path to config.yaml based on your env.
    Ex: 
    * For GG Colab: config_file_path = '/content/drive/MyDrive/Colab_env/Chatbot/code/MCAL_BOT/config.yaml'
    * For Local PC: config_file_path = './config.yaml'

### Running
Open basic_usage.py for detailed usage.

## Apendix
### Create sym_spell dictionary for correct spelling module
```sh
python create_sym_spell_dict.py update <path_to_final_data_json> <save_path>
```

### Log out to check vocabulary
```sh
python create_sym_spell_dict.py log <file_path>
```