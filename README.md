<!-- GETTING STARTED -->
# Auto
The system can be easily setup and run by using script as instructed below:
## Set Up
### For Windows
1. Open terminal
2. Run command:
```sh
./Auto_Setup_Windows.bat
```
### For Linux
1. Open terminal
2. Run command:
```sh
./Auto_Setup_Linux.sh
```

## Execute
### For Windows
1. Open terminal
2. Run command:
```sh
python Auto_Run_System.py
```
### For Linux
1. Open terminal
2. Run command:
```sh
python3 Auto_Run_System.py
```



# Manual
## Getting Started
If you want to know which packages and dependencies included, you can do it manually.
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
Need to download 2 huggingface models to folder './model':
* OpenOrca-Platypus2-13B-GPTQ
* all-mpnet-base-v2-table
```sh
python 03_Prompt\install_dependencies.py install_models ./model TheBloke/OpenOrca-Platypus2-13B-GPTQ deepset/all-mpnet-base-v2-table
```

#### NLTK Vocabularies
```sh
python 03_Prompt\install_dependencies.py install_nltk_data punkt averaged_perceptron_tagger wordnet stopwords
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



# Workaround on Lab PCs (limitations)
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

#### Install auto-gptq
1. On the local PC run
```sh
https://github.com/PanQiWei/AutoGPTQ/releases/download/v0.4.2/auto_gptq-0.4.2+cu118-cp311-cp311-win_amd64.whl
```
2. Copy the wheel to the sharing device (accessible from Lab PC)

3. Activate the virtual evironment

4. run this command:
```sh
pip install auto_gptq-0.4.2+cu118-cp311-cp311-win_amd64.whl
```


#### Install Dependencies
##### Model
Need to prepare 2 huggingface models to folder './model':
* OpenOrca-Platypus2-13B-GPTQ
* all-mpnet-base-v2-table
```sh
Copy from the shared network device DTV(\\rvc-vnas-01)(V:)\Users\hyla\AI_MCAL\Source_Code\model
```

#### NLTK Vocabularies
* corpora
* taggers
* tokenizers
```sh
Copy from the shared network device MobAP(\\rvc-vnas-01)(M:)\u\hyla\AI_CHATBOT\resources\nltk_data
```
```sh
Paste into C:\Users\rvc_sw_mss1_common\AppData\Roaming\
```

##### Spacy library:
* en_core_web_lg
* en_core_web_lg-3.5.0.dist-info
* en_core_web_sm
* en_core_web_sm-3.5.0.dist-info
```sh
Copy from the shared network device MobAP(\\rvc-vnas-01)(M:)\u\hyla\AI_CHATBOT\resources\spaCy
```
```sh
Paste into venv\Lib\site-packages\
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