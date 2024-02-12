import getpass
import os

import dotenv

dotenv.load_dotenv(".env")

# PUT YOUR API_KEY FOR TELEGRAM BOT TO .env FILE. YOUR .env SHOULD LOOK LIKE THIS: API_KEY=YOUR_KEY
API_KEY = os.environ["API_KEY"]
# DB_PASSWORD = getpass.getpass("Enter DB password: ")
info_settings = {
    "Показывать факультет": "show_faculty",
    "Показывать специальность": "show_specialization",
    "Показывать почту": "show_email",
    "Показывать группу": "show_group",
}

# Сначала нужно искать есть ли в словаре такой ключ, который нажал пользователь(защита от ошибок), а далее искать по этому ключу значение и менять в базе данных
