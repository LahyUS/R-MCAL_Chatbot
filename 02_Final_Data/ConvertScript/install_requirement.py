import re
import os
from fnmatch import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Union
from packaging import version
from huggingface_hub import HfApi, HfFolder, cached_download, hf_hub_url
import huggingface_hub

def snapshot_download(
    repo_id: str,
    revision: Optional[str] = None,
    cache_dir: Union[str, Path, None] = None,
    library_name: Optional[str] = None,
    library_version: Optional[str] = None,
    user_agent: Union[Dict, str, None] = None,
    ignore_files: Optional[List[str]] = None,
    use_auth_token: Union[bool, str, None] = None,
) -> str:
    """
	    credit/source: https://github.com/UKPLab/sentence-transformers/blob/master/sentence_transformers/util.py
    Method derived from huggingface_hub.
    Adds a new parameters 'ignore_files', which allows to ignore certain files / file-patterns
    """
    if cache_dir is None:
        cache_dir = '.'
    if isinstance(cache_dir, Path):
        cache_dir = str(cache_dir)

    if not os.path.exists(cache_dir):
        try:
            # Create the directory
            os.makedirs(cache_dir)
            print(f"The directory '{cache_dir}' has been created.")
        except OSError as e:
            print(f"An error occurred while creating the directory '{cache_dir}': {e}")
            return ''
    else:
        print(f"The directory '{cache_dir}' already exists.")

    _api = HfApi()

    token = None
    if isinstance(use_auth_token, str):
        token = use_auth_token
    elif use_auth_token:
        token = HfFolder.get_token()

    model_info = _api.model_info(repo_id=repo_id, revision=revision, token=token)

    if '/' in repo_id:
        storage_folder = os.path.join(cache_dir, repo_id.split('/')[1])
    else:
        storage_folder = os.path.join(cache_dir, repo_id)

    all_files = model_info.siblings
    # Download modules.json as the last file
    for idx, repofile in enumerate(all_files):
        if repofile.rfilename == "modules.json":
            del all_files[idx]
            all_files.append(repofile)
            break

    for model_file in all_files:
        if ignore_files is not None:
            skip_download = False
            for pattern in ignore_files:
                if fnmatch.fnmatch(model_file.rfilename, pattern):
                    skip_download = True
                    break

            if skip_download:
                continue

        url = hf_hub_url(
            repo_id, filename=model_file.rfilename, revision=model_info.sha
        )
        relative_filepath = os.path.join(*model_file.rfilename.split("/"))

        # Create potential nested dir
        nested_dirname = os.path.dirname(
            os.path.join(storage_folder, relative_filepath)
        )
        os.makedirs(nested_dirname, exist_ok=True)

        cached_download_args = {
            "url": url,
            "cache_dir": storage_folder,
            "force_filename": relative_filepath,
            "library_name": library_name,
            "library_version": library_version,
            "user_agent": user_agent,
            "use_auth_token": use_auth_token,
        }

        if version.parse(huggingface_hub.__version__) >= version.parse("0.8.1"):
            # huggingface_hub v0.8.1 introduces a new cache layout. We sill use a manual layout
            # And need to pass legacy_cache_layout=True to avoid that a warning will be printed
            cached_download_args["legacy_cache_layout"] = True

        path = cached_download(**cached_download_args)

        if os.path.exists(path + ".lock"):
            os.remove(path + ".lock")

    return storage_folder

########### Download HuggingFace model #######################
LLM_model = "TheBloke/gpt4-x-vicuna-13B-GPTQ"
embedding_model = "deepset/all-mpnet-base-v2-table"
cache_dir = "D:/Training/AI_for_MCAL/source_code/Knowledge_Transfer/MCAL_BOT_Resources/model"

print(f"Downloading:\t{LLM_model}")
model_dir = snapshot_download(repo_id=LLM_model, cache_dir=cache_dir)
print(f"Downloading:\t{embedding_model}")
embedding_model_dir = snapshot_download(repo_id=embedding_model, cache_dir=cache_dir)
##############################################################

# Need to download some additional NLP library
# - Spacy library:
# '''command line
# python -m spacy download en_core_web_lg
# python -m spacy download en_core_web_sm
# - NLTK library
# '''python

print("import nltk")
import nltk
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')