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

    await waiting_message.edit_text(text="Вы это сделали! Теперь вы авторизованы в боте. Учтите, что вы всегда можете удалить ваши данные с помощью /delete")



@dp.message(Command("settings"))
async def settings(message):
    return
    result = select_auth_info(message.from_user.id)

    if not result:
        await bot_message.edit_text("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return


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


    user_auth_info = select_auth_info(callback_query.from_user.id)

    MDL_SSP_AuthToken =  user_auth_info[0][2],
    MDL_SSP_SessID = user_auth_info[0][3],
    MOODLEID1_ = user_auth_info[0][4],
    MoodleSession = user_auth_info[0][5]
    TABNUM = user_auth_info[0][6]

    with grequests.Session() as session:
        all_courses = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getCoursesData"
        }, cookies={
            "MDL_SSP_AuthToken": user_auth_info[0][2],
            "MDL_SSP_SessID": user_auth_info[0][3],
            "MOODLEID1_": user_auth_info[0][4],
            "MoodleSession": user_auth_info[0][5]
        })

        print(all_courses)

        all_courses_json = json.loads(all_courses.text)["1"]["1"]


        text_marks = ""
        requests = []
        for course in all_courses_json:
            course_id = course["kdisc"]


            request = grequests.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
                "method": "getPerformanceData",
                "args[tabnum]": TABNUM,
                "args[kdisc]": course_id,
                "args[semester]": "1",
                "args[year]": "2023",
                "args[lang]": "6"
            }, headers={
                "Connection":"keep-alive",
                "Cookies": f"MoodleSession={MoodleSession}; MDL_SSP_AuthToken={MDL_SSP_AuthToken}; MDL_SSP_SessID={MDL_SSP_SessID}, MOODLEID1_={MOODLEID1_}"
            })

            requests.append(request)

        responses = grequests.map(requests, stream=True)


    for item in responses:
        json_course = json.loads(item.text)



        all_marks = ""
        for i in json_course:
            if i["SMARK"] == "":
                continue

            all_marks = all_marks + re.sub(CLEANR, "", f'Оценка <b>{i["SMARK"]}</b> за {i["NPOCEN_KONTRL"]}.') + "\n"


        # Проверяем даёт ли запрос на название предмета ответ
        try:
            course_name = json_course[0]["NDISC"]
        except:
            continue
        text_marks = text_marks + f"Оценки по предмету {course_name}:\n{all_marks}\n\n"

    await callback_query.message.answer(text_marks, parse_mode="HTML")  # Узнать проблему с жирным шрифтом



@dp.callback_query(F.data == "Расписание")
async def marks(callback_query):
    print(callback_query.message.chat.id)
    await callback_query.answer(text="Производим запросы...")

    # group_info = select_group_info(callback_query.from_user.id)

    # study_group = group_info[0][0]
    # lab_group_one = group_info[0][1]
    # lab_group_two = group_info[0][2]
    # faculty_group = group_info[0][3]
    # with grequests.Session() as session:
    #     group_schedule = session.get(f"https://api.grsu.by/1.x/app1/getGroupSchedule?groupId={study_group}")
    # json_group_schedule = json.loads(group_schedule.text)

    print("Заверешена загрузка")

    await callback_query.message.answer(f"авва")


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
