import getpass
import os

import dotenv

dotenv.load_dotenv(".env")

# PUT YOUR API_KEY FOR TELEGRAM BOT TO .env FILE. YOUR .env SHOULD LOOK LIKE THIS: API_KEY=YOUR_KEY
API_KEY = os.environ["API_KEY"]
DB_PASSWORD = getpass.getpass("Enter DB password: ")
# import pymysql
#
# try:
#     connection = pymysql.connect(
#         host="localhost",
#         port=3306,
#         user="root",
#         password=DB_PASSWORD,
#         database="user",
#         cursorclass=pymysql.cursors.DictCursor
#     )
# except Exception as e:
#     print(e)
