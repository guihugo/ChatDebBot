from os import getenv

from dotenv import load_dotenv

load_dotenv()

def get_url ():
    return getenv("URL")
def get_meta_key():
    return getenv("META_KEY")

def get_meta_app_secret():
    return getenv("META_APP_SECRET")

def get_phone_number():
    return getenv("PHONE_NUMBER_RECEIVER")

def get_secret_webhook():
    return getenv("SECRET_WEBHOOK")