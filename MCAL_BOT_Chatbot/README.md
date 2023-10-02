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
python -m pip install --upgrade pip
```

### Install Packages & Dependencies
#### Install packages
```sh
pip install -r requirements.txt
```

#### SQLite for deploying database
please refer to this link for the installation: https://www.tutorialspoint.com/sqlite/sqlite_installation.htm


### Create database:
#### If you need to create a new database, you could folow the below steps:
```sh
sqlite3 MCAL_BOT.db
```
Type as the below:
```sql
sqlite3> .read MCAL_Bot_Lite.sql
sqlite3> .exit
```

## Deploy the System
Our chatbot system contains 3 modules. We need to start all of them.
### Database Server
```sh
python mysqlServer.py
```

### Document Server
```sh
python documentServer.py
```

### Model Server
1. Trace to ModelServer, upload MCAL_BOT.ipynb into your Colab Notebook
2. Run from top to bottom.
3. When the final cell running, it release an ngrok URL.
4. Copy this URL and replace it in MCAL_BOT_Chatbot/config.json

### Web Server
1.  ```sh
    python main.py
    ```
2. An local host url will appear in the terminal
3. CRTL + Click on this local host.