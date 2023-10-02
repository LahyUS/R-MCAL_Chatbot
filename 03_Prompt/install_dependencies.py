# # Disable warning
import warnings
import os
import sys
warnings.filterwarnings("ignore")
from _utils import *
import nltk

##############################################################

########## Download HuggingFace model #######################
# LLM_model = "TheBloke/gpt4-x-vicuna-13B-GPTQ"
# embedding_model = "deepset/all-mpnet-base-v2-table"
# cache_dir = "./model"

# print(f"Downloading:\t{LLM_model}")
# model_dir = snapshot_download(repo_id=LLM_model, cache_dir=cache_dir)
# print(f"Downloading:\t{embedding_model}")
# embedding_model_dir = snapshot_download(repo_id=embedding_model, cache_dir=cache_dir)
# #############################################################

def download_and_install_model(model_name, cache_dir):
    model_dir = os.path.join(cache_dir, model_name)
    print(f"Downloading model {model_name}")
    snapshot_download(repo_id=model_name, cache_dir=cache_dir)

def main_install_models(cache_dir, models_to_download):
    for model_name in models_to_download:
        download_and_install_model(model_name, cache_dir)

def main_install_nltk_data(nltk_packages):
    print("Downloading NLTK data...")
    for package in nltk_packages:
        nltk.download(package)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python download_models.py command [arguments...]")
        print("Available commands: install_models, install_nltk_data")
        sys.exit(1)

    command = sys.argv[1]
    if command == "install_models":
        if len(sys.argv) < 4:
            print("Usage: python download_models.py install_models cache_dir model_name1 model_name2 ...")
            sys.exit(1)
        cache_dir = sys.argv[2]
        models_to_download = sys.argv[3:]
        main_install_models(cache_dir, models_to_download)

    elif command == "install_nltk_data":
        if len(sys.argv) < 3:
            print("Usage: python download_models.py install_nltk_data nltk_package1 nltk_package2 ...")
            sys.exit(1)
        nltk_packages = sys.argv[2:]
        main_install_nltk_data(nltk_packages)

    else:
        print(f"Unknown command: {command}")
