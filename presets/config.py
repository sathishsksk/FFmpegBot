import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
APP_ID    = int(os.getenv("APP_ID", 0))
APP_HASH  = os.getenv("APP_HASH", "")
OWNER_ID  = int(os.getenv("OWNER_ID", 0))
PORT      = int(os.getenv("PORT", 8000))
