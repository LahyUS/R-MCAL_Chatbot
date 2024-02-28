---
configs:
- config_name: default
  data_files:
  - split: train
    path: data/train-*
  - split: validation
    path: data/validation-*
dataset_info:
  features:
  - name: label
    dtype: int64
  - name: text
    dtype: string
  splits:
  - name: train
    num_bytes: 1310325
    num_examples: 1000
  - name: validation
    num_bytes: 1329205
    num_examples: 1000
  download_size: 1688812
  dataset_size: 2639530
---
# Dataset Card for "imdb-truncated"

[More Information needed](https://github.com/huggingface/datasets/blob/main/CONTRIBUTING.md#how-to-contribute-to-the-dataset-cards)