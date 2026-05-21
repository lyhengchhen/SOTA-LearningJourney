import os 
from dotenv import load_dotenv, find_dotenv

path = find_dotenv()

load_dotenv(path)
 
API_KEY = os.getenv("API_KEY")