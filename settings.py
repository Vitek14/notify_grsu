import getpass
import os

from aiogram.types import KeyboardButton

import dotenv

dotenv.load_dotenv(".env")

# PUT YOUR API_KEY FOR TELEGRAM BOT TO .env FILE. YOUR .env SHOULD LOOK LIKE THIS: API_KEY=YOUR_KEY
API_KEY = os.environ["API_KEY"]

info_settings = {
    "Показывать факультет": "show_faculty",
    "Показывать специальность": "show_specialization",
    "Показывать почту": "show_email",
    "Показывать группу": "show_group",
}

schedule_settings = {
    "Показывать УСР": "show_USR",
    "Показывать адрес": "show_adress",
    "Показывать кабинет": "show_room",
    "Показывать учителя": "show_teacher",
    "Показывать полностью дату": "show_full_data",
    "Показывать время начала": "show_start_time",
    "Показывать время конца": "show_end_time",
    "Показывать факультативные занятия": "show_facultative",
    "Показывать тип занятия": "show_lesson_type"
}

buttons = {
    "Инфо": [],
    "Расписание": [[KeyboardButton(text="Показывать УСР"), KeyboardButton(text="Показывать адрес")], [KeyboardButton(text="Показывать кабинет"), KeyboardButton(text="Показывать учителя")], [KeyboardButton(text="Показывать полностью дату"), KeyboardButton(text="Показывать время начала")], [KeyboardButton(text="Показывать время конца"), KeyboardButton(text="Показывать факультативные занятия")], [KeyboardButton(text="Показывать тип занятия")]]
}

text_settings = {
    "Инфо": "",
    "Расписание": ""
}

# keyboard_list = [[KeyboardButton(text="Показывать УСР"), KeyboardButton(text="Показывать адрес")], [KeyboardButton(text="Показывать кабинет"), KeyboardButton(text="Показывать учителя")], [KeyboardButton(text="Показывать полностью дату"), KeyboardButton(text="Показывать время начала")], [KeyboardButton(text="Показывать время конца"), KeyboardButton(text="Показывать факультативные занятия")], [KeyboardButton(text="Показывать тип занятия")]]

# Сначала нужно искать есть ли в словаре такой ключ, который нажал пользователь(защита от ошибок), а далее искать по этому ключу значение и менять в базе данных
