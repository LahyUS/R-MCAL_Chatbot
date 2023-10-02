@echo off

REM Function to check if a command is available or not
where "python" 2>nul || (
  echo Error: Python is not installed. Please install it before proceeding.
  exit /b 1
)

REM Function to display error messages
echo Creating and activating virtual environment...
python -m venv .\venv
call .\venv\Scripts\activate
python -m pip install --upgrade pip

REM Function to install packages from requirements.txt
echo Installing packages from requirements.txt...
pip install -r requirements.txt

REM Function to install the required models and libraries
echo Installing huggingface models...
python 03_Prompt\install_dependencies.py install_models ./model TheBloke/OpenOrca-Platypus2-13B-GPTQ deepset/all-mpnet-base-v2-table

echo Installing NLTK vocabularies...
python 03_Prompt\install_dependencies.py install_nltk_data punkt averaged_perceptron_tagger wordnet stopwords

echo Installing Spacy libraries...
python -m spacy download en_core_web_lg
python -m spacy download en_core_web_sm

REM Main script
