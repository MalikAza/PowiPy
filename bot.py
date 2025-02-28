import os
from dotenv import load_dotenv
load_dotenv()

from src import Client

def main():
    token = os.getenv('TOKEN')
    bot = Client(command_prefix="!")
    bot.run(token, log_handler=None)

if __name__ == '__main__':
    main()