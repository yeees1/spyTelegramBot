import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
CR_API_TOKEN = os.getenv("CR_API_TOKEN")
CR_BASE_URL = "https://proxy.royaleapi.dev"
OFFICIAL_CARDS_URL = f"{CR_BASE_URL}/v1/cards"
DESCRIPTIONS_URL = "https://royaleapi.github.io/cr-api-data/json/cards.json"
admin_id = os.getenv("ADMIN_ID")
MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DB = os.getenv("MYSQL_DB", "botdb")
MYSQL_USER = os.getenv("MYSQL_USER", "botuser")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD")