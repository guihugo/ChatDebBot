from os import getenv

from dotenv import load_dotenv

load_dotenv()

def get_meta_key():
    return getenv("META_KEY")

def get_phone_number():
    return getenv("PHONE_NUMBER_RECEIVER")