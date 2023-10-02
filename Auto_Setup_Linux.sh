#!/bin/bash

# Function to check if a command is available or not
function command_exists() {
  command -v "$1" >/dev/null 2>&1
}

# Function to display error messages
function show_error() {
  echo "Error: $1"
  exit 1
}

# Function to create a directory if it does not exist
function create_directory_if_not_exists() {
  if [ ! -d "$1" ]; then
    echo "Creating $1 directory..."
    mkdir -p "$1"
  else
    echo "$1 directory already exists."
  fi
}

# Function to create virtual environment and activate it
function create_and_activate_venv() {
  echo "Creating and activating virtual environment..."
  python3 -m venv ./venv
  source venv/Scripts/activate
  python3 -m pip install --upgrade pip
}

# Function to install packages from requirements.txt
function install_packages() {
  echo "Installing packages from requirements.txt..."
  pip install -r requirements.txt
}

# Function to install the required models and libraries
function install_dependencies() {
  echo "Installing huggingface models..."
  python3 03_Prompt/install_dependencies.py install_models ./model TheBloke/gpt4-x-vicuna-13B-GPTQ deepset/all-mpnet-base-v2-table

  echo "Installing NLTK vocabularies..."
  python3 03_Prompt/install_dependencies.py install_nltk_data punkt averaged_perceptron_tagger wordnet stopwords

  echo "Installing Spacy libraries..."
  python3 -m spacy download en_core_web_lg
  python3 -m spacy download en_core_web_sm
}

# Main script

# Check if required dependencies are installed
check_dependency python3

# Create and activate virtual environment
create_and_activate_venv

# Install packages from requirements.txt
install_packages

# Install the required models and libraries
install_dependencies
