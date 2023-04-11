My personnal (but not main one) Discord's Bot, written in Python, from scratch.

This repo is for personnal use and you may not be able to fully used this bot, unless you know what to do with the environment variables and the lines who depends on it.

# Configuration
[Python](https://www.python.org/) version needed: 3.8 | 3.9 | 3.10

Those versions are needed to run [discord.py](https://github.com/Rapptz/discord.py) v2.*

You need to create a Discord App in the [Discord Developer Portal](https://discord.com/developers/), create a bot app and check all the Intents. *(Also uncheck `public bot`)*

# Installation
*It is recommended to build a python app in a virtual environment with [python-venv](https://docs.python.org/fr/3/library/venv.html).*

Clone the project:
```bash
git clone https://github.com/MalikAza/PowiPy.git
```
Install the requirements:
```bash
pip3 install -r requirements.txt
```
Change the **.env.example** file to **.env** and change its content.

**YOUR_DISCORD_APP_INVITE_LINK** must be something like:
https://discord.com/api/oauth2/authorize?client_id=client_id_from_discord_api_page&permissions=0&scope=bot%20applications.commands

# Running
```bash
cd PowiPy/
python3 bot.py
```
*You may need to specify your python version. Ex: `python3.8 bot.py`*