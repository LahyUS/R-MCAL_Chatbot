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


## Usage
### Configuration
1. Open extern_variables.py, then modify:
    * OUTPUT_PATH: path to the output folder.
    * CONFIG_PATH: relative path to the config.yaml.
2. Detailed config: Open config.yaml and change paths to the required fields.

### Final Data Generation
1. Open main.py
2. Choose the approriate converter type.
3. Fill module name of the current middle data. 
4. Run command
```sh
python main.py
```