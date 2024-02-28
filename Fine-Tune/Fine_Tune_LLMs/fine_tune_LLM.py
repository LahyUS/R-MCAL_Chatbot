
#*********************************************************************************************************
#**                                                Import                                               **
#*********************************************************************************************************
from datasets import load_dataset, DatasetDict, Dataset, load_from_disk
from peft import PeftModel, PeftConfig, get_peft_model, LoraConfig
import evaluate
import torch
import numpy as np
import os
from transformers import (
    AutoTokenizer,
    AutoConfig, 
    AutoModelForSequenceClassification,
    DataCollatorWithPadding,
    TrainingArguments,
    Trainer)

lets_train = False

model_checkpoint = "C:\\Users\\rvc_sw_mss1_common\\Desktop\\test\\mcal-guru\\model\\distilbert-base-uncased"
dataset_directory = "C:\\Users\\rvc_sw_mss1_common\\Desktop\\test\\mcal-guru\\Fine_Tune\\Datasets\\Saved_datasets\\shawhin-imdb-truncated"
dataset_name = 'shawhin/imdb-truncated'
metrics_dir = "C:\\Users\\rvc_sw_mss1_common\\Desktop\\test\\mcal-guru\\Fine_Tune\\evaluate\\metrics\\accuracy\\accuracy.py"
model_save_path = "C:\\Users\\rvc_sw_mss1_common\\Desktop\\test\\mcal-guru\\Fine_Tune\\Trained_models\\distilbert-base-uncased\\"

#*********************************************************************************************************
#**                                                Base Model                                           **
#*********************************************************************************************************
# define label maps
id2label = {0: "Negative", 1: "Positive"}
label2id = {"Negative":0, "Positive":1}

# generate classification model from model_checkpoint
model = AutoModelForSequenceClassification.from_pretrained(
    model_checkpoint, num_labels=2, id2label=id2label, label2id=label2id)


#*********************************************************************************************************
#**                                                Load Data                                            **
#*********************************************************************************************************
# load dataset

if os.path.exists(dataset_directory) and os.listdir(dataset_directory):
    print("Dataset already downloaded. Loading from disk")
    dataset = load_from_disk(dataset_directory)
    print("Dataset has been loaded")
else:
    print("Downloading dataset...")
    dataset = load_dataset(dataset_name)
    print("Saving dataset to disk...")
    dataset.save_to_disk(dataset_directory)
    
print(dataset)

# dataset = 
# DatasetDict({
#     train: Dataset({
#         features: ['label', 'text'],
#         num_rows: 1000
#     })
#     validation: Dataset({
#         features: ['label', 'text'],
#         num_rows: 1000
#     })
# }) 

#*********************************************************************************************************
#**                                                Preprocess Data                                      **
#*********************************************************************************************************
# create tokenizer
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint, add_prefix_space=True)

# create tokenize function
def tokenize_function(examples):
    # extract text
    text = examples["text"]

    #tokenize and truncate text
    tokenizer.truncation_side = "left"
    tokenized_inputs = tokenizer(
        text,
        return_tensors="np",
        truncation=True,
        max_length=512
    )

    return tokenized_inputs

# add pad token if none exists
if tokenizer.pad_token is None:
    tokenizer.add_special_tokens({'pad_token': '[PAD]'})
    model.resize_token_embeddings(len(tokenizer))

# tokenize training and validation datasets
tokenized_dataset = dataset.map(tokenize_function, batched=True)
tokenized_dataset

# tokenized_dataset = 
# DatasetDict({
#     train: Dataset({
#        features: ['label', 'text', 'input_ids', 'attention_mask'],
#         num_rows: 1000
#     })
#     validation: Dataset({
#         features: ['label', 'text', 'input_ids', 'attention_mask'],
#         num_rows: 1000
#     })
# })

# create data collator
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

#*********************************************************************************************************
#**                                                Evaluation Metrics                                   **
#*********************************************************************************************************
# import accuracy evaluation metric
accuracy = evaluate.load(metrics_dir)

# define an evaluation function to pass into trainer later
def compute_metrics(p):
    predictions, labels = p
    predictions = np.argmax(predictions, axis=1)

    return {"accuracy": accuracy.compute(predictions=predictions, 
                                          references=labels)}
                                          
                                          

#*********************************************************************************************************
#**                                                Untrained Model Performance                          **
#*********************************************************************************************************
# define list of examples
text_list = ["It was good.", "Not a fan, don't recommed.", 
"Better than the first one.", "This is not worth watching even once.", 
"This one is a pass."]

print("Untrained model predictions:")
print("----------------------------")
for text in text_list:
    # tokenize text
    inputs = tokenizer.encode(text, return_tensors="pt")
    # compute logits
    logits = model(inputs).logits
    # convert logits to label
    predictions = torch.argmax(logits)

    print(text + " - " + id2label[predictions.tolist()])

# Output:
# Untrained model predictions:
# ----------------------------
# It was good. - Negative
# Not a fan, don't recommed. - Negative
# Better than the first one. - Negative
# This is not worth watching even once. - Negative
# This one is a pass. - Negative


#*********************************************************************************************************
#**                                                Fine-tuning with LoRA                                **
#*********************************************************************************************************
peft_config = LoraConfig(task_type="SEQ_CLS", # sequence classification
                        r=4, # intrinsic rank of trainable weight matrix
                        lora_alpha=32, # this is like a learning rate
                        lora_dropout=0.01, # probablity of dropout
                        target_modules = ['q_lin']) # we apply lora to query layer only


model = get_peft_model(model, peft_config)
model.print_trainable_parameters()

# trainable params: 1,221,124 || all params: 67,584,004 || trainable%: 1.8068239934408148


# hyperparameters
lr = 1e-3 # size of optimization step 
batch_size = 4 # number of examples processed per optimziation step
num_epochs = 10 # number of times model runs through training data

# define training arguments
training_args = TrainingArguments(
    output_dir= model_checkpoint + "-lora-text-classification",
    learning_rate=lr,
    per_device_train_batch_size=batch_size, 
    per_device_eval_batch_size=batch_size,
    num_train_epochs=num_epochs,
    weight_decay=0.01,
    evaluation_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
)


# creater trainer object
trainer = Trainer(
    model=model, # our peft model
    args=training_args, # hyperparameters
    train_dataset=tokenized_dataset["train"], # training data
    eval_dataset=tokenized_dataset["validation"], # validation data
    tokenizer=tokenizer, # define tokenizer
    data_collator=data_collator, # this will dynamically pad examples in each batch to be equal length
    compute_metrics=compute_metrics, # evaluates model using compute_metrics() function from before
)


# train model
trainer.train()


test_corpus = [
    "hey, do not disturb me",
    "are you crazy",
    "I love you so so much",
    "How can I do that?",
    "Boring",
    "Oh, what's next?"
]

for i in test_corpus:
    print("\n", i)
    
    
#*********************************************************************************************************
#**                                                Trained Model Performance                            **
#*********************************************************************************************************
model.to('cpu') # moving to mps for Mac (can alternatively do 'cpu')

print("Trained model predictions:")
print("--------------------------")
for text in test_corpus:
    inputs = tokenizer.encode(text, return_tensors="pt").to("cpu") # moving to mps for Mac (can alternatively do 'cpu')

    logits = model(inputs).logits
    predictions = torch.max(logits,1).indices

    print(text + " - " + id2label[predictions.tolist()[0]])

# Output:
# Trained model predictions:
# ----------------------------
# It was good. - Positive
# Not a fan, don't recommed. - Negative
# Better than the first one. - Positive
# This is not worth watching even once. - Negative
# This one is a pass. - Positive # this one is tricky