import grequests

import aiogram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import asyncio

# Импорт функций
from functions.auth import auth
from functions.select_info import select_auth_info, select_group_info, get_web_user_info
from functions.parse_marks import get_raw_marks, proccess_marks
from settings import API_KEY, DB_PASSWORD
from functions.notifications import timer

# Импорт даты чтобы показывать расписание более приятным способом
from datetime import date, datetime, timedelta

import sqlite3

# Для нормальной обработки контента
import json

# Для чистки текста от html тегов
import re
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

bot = Bot(API_KEY)

dp = Dispatcher()


@dp.message(Command("agree"))
async def agree_command(message):
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Я согласен", callback_data="Согласие")

    markup.inline_keyboard.append([btn1])

    await message.answer(text="Нажимая кнопку ниже, вы соглашаетесь с тем, что бот и разработчик смогут видеть, анализировать и использовать личные данные(логин, пароль, ваши данные об оценках, ваше имя, фамилия, отчество, а также другие личные данные)", protect_content=True, reply_markup=markup)


def set_default_preferences(tg_id):
    # Подключаемся к базе данных с данными пользователя
    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    # cursor.execute("SELECT username, password, MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession FROM user_data WHERE tg_id=?", (tg_id,))
    cursor.execute("INSERT INTO user_preferences(user_id) VALUES(?)", (tg_id))
    # result = cursor.fetchall()
    # cursor.commit()
    cursor.close()
    # return result

@dp.message(Command("login"))
async def login_command(message):
    text = message.text.split(" ")
    if len(text) < 3 or len(text) > 3:
        await message.answer(text="Неправильно введены данные!")
        return
    login = text[1]
    password = text[2]


    user_id = message.from_user.id
    await message.delete()
    waiting_message = await bot.send_message(chat_id=message.from_user.id, text="Пробуем войти, это может занять некоторое время ⌛️")

    # Функция входа
    text = auth(user_id, login, password)

    # Если функция вернула текст, то значит что неверная авторизация.
    # Поэтому отправляем сообщение об этом
    if type(text) == str:
        await waiting_message.edit_text(text=text)
        return

    # set_default_preferences(user_id)

    await waiting_message.edit_text(text="Вы это сделали! Теперь вы авторизованы в боте. Учтите, что вы всегда можете удалить ваши данные с помощью /delete")





def select_settins_info(tg_id):
    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    cursor.execute("SELECT show_today_at_end, show_USR, show_full_schedule_for_next_days FROM user_prefrences WHERE user_id=?", (tg_id,))
    result = cursor.fetchall()
    cursor.close()
    return result

@dp.message(Command("settings"))
async def settings(message):
    return
    result = select_auth_info(message.from_user.id)

    if not result:
        await bot_message.edit_text("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return

@dp.message(Command("info"))
async def start_command(message):

    bot_message = await message.answer(text="Производим запросы...", protect_content=True)


    # Есть повторение в коде. Повторяется где настройки
    result = select_auth_info(message.from_user.id)

    if not result:
        await bot_message.edit_text("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return

    info = get_web_user_info(result)


    try:
        info["userInfo"]
    except:
        await bot_message.edit_text("Видимо токен устарел, пробуем обновить...")
        auth(message.from_user.id, result[0][0], result[0][1])
        result = select_auth_info(message.from_user.id)
        info = get_web_user_info(result)


    useful_info = info["userInfo"]
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Оценки", callback_data="Оценки")
    btn2 = aiogram.types.InlineKeyboardButton(text="Расписание", callback_data="Расписание")

    markup.inline_keyboard.append([btn1, btn2])

    await bot_message.edit_text(f"""
ФИО: {useful_info["FIO_R"]}
Курс: {useful_info["N_D"]}
Факультет: {useful_info["N_OTDEL"]}
Специальность: {useful_info["NNAUCH"]}
EMAIL: {useful_info["EMAIL"]}
Группа: {useful_info["N_GRYP"]}""", reply_markup=markup, protect_content=True)


@dp.callback_query(F.data == "Оценки")
async def user_marks(callback_query):
    await callback_query.answer(text="Производим запросы, это занимает обычно 5 секунд...")


    user_id = callback_query.from_user.id
    user_auth_info = select_auth_info(user_id)

    # Получаем необработанные оценки
    raw_marks = await get_raw_marks(user_auth_info)
    text_marks =  proccess_marks(user_id, raw_marks, False)

    await callback_query.message.answer(text_marks, parse_mode="HTML")  # Узнать проблему с жирным шрифтом


@dp.callback_query(F.data == "Расписание")
async def marks(callback_query):
    print(callback_query.message.chat.id)
    await callback_query.answer(text="Производим запросы...")

    group_info = select_group_info(callback_query.from_user.id)

    print(group_info[0])
    study_group = group_info[0][0]
    lab_group_one = group_info[0][1]
    lab_group_two = group_info[0][2]
    lab_group_three = group_info[0][3]
    lab_group_four = group_info[0][4]
    faculty_group = group_info[0][5]

    
    with grequests.Session() as session:
        group_schedule = session.get(f"https://api.grsu.by/1.x/app1/getGroupSchedule?groupId={study_group}")
    json_group_schedule = json.loads(group_schedule.text)

    print("Заверешена загрузка")

    today_raw = datetime.today() # .strftime('%Y-%m-%d')
    yesterday_raw = today_raw - timedelta(1)
    tommorow_raw = today_raw + timedelta(1)

    today = today_raw.strftime('%Y-%m-%d')
    yesterday = yesterday_raw.strftime('%Y-%m-%d')
    tommorow = tommorow_raw.strftime('%Y-%m-%d')

    text_lessons = ""
    today_lessons = ""
    tommorow_lessons = ""
    date_counter = 0
    for item in json_group_schedule["days"]:
        print(item["date"])
        if item["date"] == today:
            # text_lessons = text_lessons + "\n\n" + "СЕГОДНЯ" + "\n"
            today_lessons = today_lessons + "\n\n" + "СЕГОДНЯ" + "\n"
            date_counter = 2
        elif item["date"] == yesterday:
            text_lessons = text_lessons + "\n\n" + "Вчера" + "\n"
            date_counter = 1
        elif item["date"] == tommorow:
            # text_lessons = text_lessons + "\n\n" + "Завтра" + "\n"
            tommorow_lessons = tommorow_lessons + "\n\n" + "Завтра" + "\n"
            date_counter = 3
        else:
            text_lessons = text_lessons + "\n\n" + item["date"] + "\n"
            date_counter = 0

        # Перебор для уроков
        for lesson in item["lessons"]:
            if (lesson["subgroup"]["id"] == lab_group_one) or (lesson["subgroup"]["id"] == lab_group_two) or (lesson["subgroup"]["id"] == lab_group_three) or (lesson["subgroup"]["id"] == lab_group_four) or (lesson["subgroup"]["id"] == faculty_group) or (lesson["subgroup"]["id"] == "0"):
                if date_counter == 2:
                    today_lessons = today_lessons + f"{lesson['title']} ({lesson['timeStart']} - {lesson['timeEnd']}) - {lesson['address']}\n"
                elif date_counter == 3:
                    tommorow_lessons = tommorow_lessons + f"{lesson['title']} ({lesson['timeStart']} - {lesson['timeEnd']}) - {lesson['address']}\n"
                else:
                    text_lessons = text_lessons + f"{lesson['title']} ({lesson['timeStart']} - {lesson['timeEnd']}) - {lesson['address']}\n"
            else:
                continue

    await callback_query.message.answer(f"{text_lessons}\n{tommorow_lessons}\n{today_lessons}")


async def start():

    print("Бот готов к работе")
    asyncio.create_task(timer(bot, 300))
    loop = asyncio.get_event_loop()
    await dp.start_polling(bot)
    

if __name__ == "__main__":
    asyncio.run(start())
