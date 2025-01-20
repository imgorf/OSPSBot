import os
from dotenv import load_dotenv

load_dotenv() #loads env file
api_key=os.getenv('OSPSCBot_Key') #imports api key from env file
print(api_key)