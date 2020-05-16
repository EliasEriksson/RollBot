import json
from bot.bot import Client


with open("token.json") as f:
    token = json.load(f)


Client().run(token)
