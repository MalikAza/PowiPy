import os
from dotenv import load_dotenv
load_dotenv()

from src import Client

token = os.getenv('TOKEN')
bot = Client(command_prefix=";")
bot.run(token, log_handler=None)