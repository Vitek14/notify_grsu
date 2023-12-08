import grequests

import aiogram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import asyncio

import sqlite3

# Импорт даты чтобы показывать расписание более приятным способом
from datetime import date, datetime, timedelta

# Для нормальной обработки контента
import json

# Для чистки текста от html тегов
import re
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

bot = Bot("6315468656:AAElByUicc2WKyoydPfj1yvhsJfGhYAMrf4")

dp = Dispatcher()

@dp.message(Command("login"))
async def login_command(message):
    # await message.text
    text = message.text.split(" ")
    if len(text) !=3:
        print(len(text))
        await message.answer(text="Неправильно введены данные!")
        return

    # print("ААА")
    login = text[1]
    password = text[2]

    user_id = message.from_user.id
    await message.delete()
    waiting_message = await bot.send_message(chat_id=message.from_user.id, text="Пробуем войти, это может занять некоторое время ⌛️")

    # Функция входа
    text = auth(user_id, login, password)

    if type(text) == str:
        await waiting_message.edit_text(text=text)
        return

    await waiting_message.edit_text(text="Вы это сделали! Теперь вы авторизованы в боте. Учтите, что вы всегда можете удалить ваши данные с помощью /delete_data")


def select_auth_info(tg_id):
    # Подключаемся к базе данных с данными пользователя
    db_connection = sqlite3.connect("presentation.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    cursor.execute("SELECT login, password FROM user WHERE tg_id=?", (tg_id,))
    result = cursor.fetchall()
    cursor.close()
    return result


def auth(user_id, login, password):
    if login != "test" and password != "test":
        return "Проверьте данные логина и пароля"

    db_connection = sqlite3.connect("presentation.db", timeout=10.0)
    cursor = db_connection.cursor()
    cursor.execute("SELECT login, password FROM user WHERE tg_id=?", (user_id,))
    result = cursor.fetchone()
    if result:
        cursor.execute("""UPDATE user SET login=?,
password=?,
WHERE tg_id=?""", (login, password, user_id))
    else:
        cursor.execute("INSERT INTO user VALUES (?, ?, ?)", (login, password, user_id))

    db_connection.commit()


@dp.message(Command("delete_data"))
async def delete_command(message):
    result = select_auth_info(message.from_user.id)

    if not result:
        await message.answer("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return


    db_connection = sqlite3.connect("presentation.db", timeout=10.0)
    cursor = db_connection.cursor()
    cursor.execute("SELECT login, password FROM user WHERE tg_id=?", (message.from_user.id,))
    result = cursor.fetchone()
    cursor.execute("""DELETE FROM user WHERE tg_id=?""", (message.from_user.id,))

    db_connection.commit()
    await message.answer("Ваши данные удалены.")

    # cursor.close()

@dp.message(Command("settings"))
async def settings_command(message):
    await message.answer("Вы сейчас находитесь в демонстрационном режиме, поэтому настройки недоступны.")

@dp.message(Command("start"))
async def help_command(message):
    await message.answer("Привет, я телеграмм-бот для организации твоего учебного времени! Я буду тебя оповещать о новых оценках, изменении в расписании и многом другом! Ты также можешь самостоятельно это всё просматривать.\n*Демонстрационный режим*\n<b>Введите /login test test чтобы войти в систему</b>", parse_mode="HTML")

@dp.message(Command("feedback"))
async def feedback_command(message):

    text = message.text.split(" ")
    # print(len(text))
    if len(text) < 2:
        await message.answer(text="Введите отзыв который вы хотите отправить!")
        return

    await message.answer("Спасибо, вы помогаете нам стать лучше!")
    await bot.send_message(chat_id=624374169, text=message.text)

@dp.message(Command("info"))
async def start_command(message):

    bot_message = await message.answer(text="Производим запросы...", protect_content=True)


    # Есть повторение в коде. Повторяется где настройки
    result = select_auth_info(message.from_user.id)

    if not result:
        await bot_message.edit_text("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return


    # info = get_web_user_info(result)
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Оценки", callback_data="Оценки")
    btn2 = aiogram.types.InlineKeyboardButton(text="Расписание", callback_data="Расписание")

    markup.inline_keyboard.append([btn1, btn2])

    await bot_message.edit_text(f"""
ФИО: Иванов Александр Анатольевич
Курс: Студент 1 курса д/о
Факультет: Физико-технический факультет
Специальность: Информационно-измерительные приборы и системы
EMAIL: example_email@student.grsu.by
Группа: СДП-ИИПС""", reply_markup=markup, protect_content=True)

@dp.callback_query(F.data == "Оценки")
async def user_marks(callback_query):
    await callback_query.answer(text="Производим запросы, это занимает обычно 5 секунд...")

# Есть повторение в коде. Повторяется где настройки
    result = select_auth_info(callback_query.from_user.id)

    if not result:
        await callback_query.message.answer("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return

    await callback_query.message.answer(f"""
Математика:
<b>8</b> за 15.11.2023(Контрольное занятие)
<b>10</b> за 01.12.2023(Опрос)

Информатика:
<b>10</b> за 14.11.2023(Опрос)

Инженерная графика:
<b>8</b> за 16.11.2023(Контрольное занятие)

Физика:
<b>9</b> за 14.11.2023(Опрос)
<b>8</b> за 16.11.2023(Опрос)

Химия:
<b>7</b> за 01.12.2023(Контрольное занятие)

Иностранный язык(Английский язык):
<b>10</b> за 12.11.2023(Опрос)
<b>10</b> за 14.11.2023(Опрос)""", parse_mode="HTML")  # Узнать проблему с жирным шрифтом



@dp.callback_query(F.data == "Расписание")
async def marks(callback_query):
    print(callback_query.message.chat.id)
    await callback_query.answer(text="Производим запросы...")

# Есть повторение в коде. Повторяется где настройки
    result = select_auth_info(callback_query.from_user.id)

    if not result:
        await callback_query.message.edit_text("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return

    await callback_query.message.answer(text=f"<b>Понедельник</b>:\nОсновы права(сем.занятие) - 10.05 - 11.30 на Ожешко, 22 каб. 122\n\n<b>Вторник:</b>\nИнженерная графика(практ.зан) - 08.30 - 09.55 на БЛК, 5 каб. 206\nИнженерная графика(практ.зан) - 10.05 - 11.30 на БЛК, 5 каб. 206\nМатематика(практ.зан) - 11.40 - 13.05 на БЛК, 5 каб. 408\n\n<b>Среда:</b>\nИнформатика(лаб) - 08.30 - 09.55 на БЛК, 5 каб. 212\nИнформатика(лаб) - 10.05 - 11.30 на БЛК, 5 каб. 212\n\n<b>Четверг:</b>\nИностранный язык(практ. зан) - 08.30 - 09.55 на БЛК, 5 каб. 305\nИностранный язык(практ. зан) - 10.05 - 11.30 на БЛК, 5 каб. 305\n\n<b>Пятница:</b>\nФизика(лекция) - 08.30 - 09.55 на Ожешко, 22 каб. 122\nИнформатика(лекция) - 10.05 - 11.30 на Ожешко, 22 каб. 122\nИнформатика(лекция) - 11.40 - 13.05 на Ожешко, 22 каб. 122\n", parse_mode="HTML")
# .message.answer(f"авва")


@dp.message(Command("stop"))
async def stop_command(message):
    text = message.text.split(" ")
    if len(text) !=2:
        # print(len(text))
        # await message.answer(text="Неправильно введены данные!")
        return

    login = text[1]
    # password = text[2]
    if login == "1937":
        quit()
    # exit()


async def start():
    # bot = aiogram.Bot("6764455698:AAHWL7Zs60lWkqo8KdRcCfDs2yrd8YoxmEU")
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Это неверная информация", callback_data="Сегодня")
    btn2 = aiogram.types.InlineKeyboardButton(text="Оценки по этому предмету", callback_data="Завтра")

    markup.inline_keyboard.append([btn1, btn2])

    print("Бот готов к работе")

    # await bot.send_message(chat_id=624374169, text="Утепляйтесь! Сегодня более чем на 5 градусов холоднее, чем вчера!", reply_markup=markup, parse_mode="HTML")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start())
