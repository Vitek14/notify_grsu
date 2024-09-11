import getpass
import os

from aiogram.types import KeyboardButton

import dotenv

dotenv.load_dotenv(".env")

# PUT YOUR API_KEY FOR TELEGRAM BOT TO .env FILE. YOUR .env SHOULD LOOK LIKE THIS: API_KEY=YOUR_KEY
API_KEY = os.environ["API_KEY"]

settings_dict = {
    "Инфо": {
        "text": "Данные настройки затронут команду /info",
        "Показывать факультет": "show_faculty",
        "Показывать специальность": "show_specialization",
        "Показывать почту": "show_email",
        "Показывать группу": "show_group"
    },
    "Расписание": {
        "text": "Данные настройки влияют на отображение расписания."
                "Большинство из них влияет только на текстовую версию",
        "Показывать УСР": "show_USR",
        "Показывать адрес": "show_address",
        "Показывать кабинет": "show_room",
        "Показывать учителя": "show_teacher",
        "Показывать полностью дату": "show_full_data",
        "Показывать время начала": "show_start_time",
        "Показывать время конца": "show_end_time",
        "Показывать факультативные занятия": "show_facultative",
        "Показывать тип занятия": "show_lesson_type",
    },
    "Уведомления": {
        "text": "Данные настройки повлияют на уведомления от бота",
        "Уведомлять об изменении расписания на N дней вперёд": "days_notify",
        "Уведомлять об изменении расписания на N дней назад": "back_days_notify"
    }
}

settings_buttons = {
    "Инфо": [
        [KeyboardButton(text="Показывать факультет"), KeyboardButton(text="Показывать специальность")],
        [KeyboardButton(text="Показывать почту"), KeyboardButton(text="Показывать группу")],
        [KeyboardButton(text="Убрать это..."), KeyboardButton(text="Назад")]
    ],
    "Расписание": [
        [KeyboardButton(text="Показывать УСР"), KeyboardButton(text="Показывать адрес")],
        [KeyboardButton(text="Показывать кабинет"), KeyboardButton(text="Показывать учителя")],
        [KeyboardButton(text="Показывать полностью дату"), KeyboardButton(text="Показывать время начала")],
        [KeyboardButton(text="Показывать время конца"), KeyboardButton(text="Показывать факультативные занятия")],
        [KeyboardButton(text="Показывать тип занятия")],
        [KeyboardButton(text="Убрать это..."), KeyboardButton(text="Назад")]
    ],
    "Уведомления": [
        [KeyboardButton(text="Уведомлять об изменении расписания на N дней вперёд")],
        [KeyboardButton(text="Уведомлять об изменении расписания на N дней назад")]
    ]
}

proxy_list_http = [
    "http://3.21.101.158:3128",
    "http://3.90.100.12:3128",
    "http://35.185.196.38:3128",
]

proxy_list_https = [
    "http://35.237.210.215:3128",
    "http://35.185.196.38:3128",
    "http://172.96.117.205:38001",
]

logging_level = "WARNING"  # Обычно не нужно менять

schedule_check_interval = 8  # В минутах

base_engine = "sqlite:///user.db"

# TODO: Сделать автоматические обновление групп студента каждые N дней
# TODO: Сделать кулдауд команд.
# TODO: Сделать кнопки в настройках для уведомлений об изменениях
# TODO: Сделать возможность не показывать текст/картинку
# TODO: Сделать быструю команду для расписания
# TODO: Добавить возможность открыть полное расписание, если изменения на один день только
# TODO: Сделать шифрование логина и пароля
# TODO: Переделать оценки
