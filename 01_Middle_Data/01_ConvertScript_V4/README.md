<!-- GETTING STARTED -->
## Getting Started
This is an example of how you may give instructions on setting up your project locally.
To get a local copy up and running follow these simple example steps.

### Create virtual enviroment
```sh
python -m venv ./venv
cd venv
cd Scripts
activate
```

### Install Packages & Dependencies
#### Upgrade Pip
```sh
python -m pip install --upgrade pip
```

#### Install packages
```sh
pip install -r requirements.txt
```

## Usage
You could run on 2 mode:

### Terminal command
python <module>.py --file_format --path_to_data --<update/not>
Ex: python Autosar2middledatabase.py --pdf --D:/Training/AI_for_MCAL/source_code/Knowledge_Transfer/MCAL_BOT_Resources/0_Input_data/ --update
Ex: python UM2middledatabase.py --pdf --D:/Training/AI_for_MCAL/source_code/Knowledge_Transfer/MCAL_BOT_Resources/0_Input_data/ --

### Launch Debugger
1. Go to "Run" -> "Add Configuration..."
2. Replace the args field by the below:
```json
"args": ["--pdf",
            "D:/Training/AI_for_MCAL/source_code/Knowledge_Transfer/MCAL_BOT_Resources/0_Input_data/",
            "--"
]
```
3. Go to "Run" -> "Start Withou Debugging"