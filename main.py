import grequests

import aiogram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import asyncio

# Импорт функций
from functions.auth import auth
from functions.select_info import select_auth_info, select_group_info


# Импорт даты чтобы показывать расписание более приятным способом
from datetime import date, datetime, timedelta

import sqlite3

# Для нормальной обработки контента
import json

# Для чистки текста от html тегов
import re
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

bot = Bot("6315468656:AAElByUicc2WKyoydPfj1yvhsJfGhYAMrf4")

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
    # await message.text
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


def get_web_user_info(user_auth_info):
    with grequests.Session() as sess:
        info_about_student = sess.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getEmployeesData"
        }, cookies={
            "MDL_SSP_AuthToken": user_auth_info[0][2],
            "MDL_SSP_SessID": user_auth_info[0][3],
            "MOODLEID1_": user_auth_info[0][4],
            "MoodleSession": user_auth_info[0][5]
        })
        info = json.loads(info_about_student.text)
    return info


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

        # Тут получили какие предметы на специальности
        all_courses_json = json.loads(all_courses.text)["1"]["1"]


        text_marks = ""
        requests = []

        # Создание списка с запросами(requests) на каждый предмет, чтобы потом быстро получить данные о каждом предмете на специальности
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


    
    # задаем переменные с данными об оценках
    # student_subject = "Математика"
    # student_marks = [6, 9, 10, 6, 7]
    # student_marks_dates = ["11-10", "16-10", "04-11", "16-11", "02-12"]
    # user_id = 1
    # # создаем список кортежей с данными
    
    # Это уже парсинг каждого предмета

    db = sqlite3.connect("user.db")
    cursor = db.cursor()
    for item in responses:
        json_course = json.loads(item.text)


        all_marks = ""
        # student_marks = []  # Аналог all_marks, потом надо убрать all_marks, если с student_marks будет нормально работать

        student_marks = []
        student_marks_dates = []

        

        
        for i in json_course:
            if i["SMARK"] == "":
                continue
            student_marks.append(i["SMARK"])
            student_marks_dates.append(i["DATE_ACADEMIC"])
            all_marks = all_marks + re.sub(CLEANR, "", f'Оценка <b>{i["SMARK"]}</b> за {i["NPOCEN_KONTRL"]}.') + "\n"


        # Проверяем даёт ли запрос на название предмета ответ
        try:
            course_name = json_course[0]["NDISC"]  # Убрать
            student_subject = json_course[0]["NDISC"]  
        except:
            continue


        data = [(student_subject, student_marks[i], student_marks_dates[i], user_id) for i in range(len(student_marks))]
        # вставляем все данные об оценках в таблицу grades одним запросом
        cursor.executemany("INSERT INTO grades (subject, mark, date, user_id) VALUES (?, ?, ?, ?)", data)
   

        text_marks = text_marks + f"Оценки по предмету {course_name}:\n{all_marks}\n\n"

    db.commit()
    db.close()
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


@dp.message(Command("schedule"))
async def schedule_command(message):
    await message.answer(text=f"<b>ЗАВТРА</b>:\nОсновы права(сем.занятие) - 10.05 - 11.30 на Ожешко, 22 каб. 122\n\n<b>Вторник:</b>\nИнженерная графика(практ.зан) - 08.30 - 09.55 на БЛК, 5 каб. 206\nИнженерная графика(практ.зан) - 10.05 - 11.30 на БЛК, 5 каб. 206\nМатематика(практ.зан) - 11.40 - 13.05 на БЛК, 5 каб. 408\n\n<b>Среда:</b>\nИнформатика(лаб) - 08.30 - 09.55 на БЛК, 5 каб. 212\nИнформатика(лаб) - 10.05 - 11.30 на БЛК, 5 каб. 212\n\n<b>Четверг:</b>\nИностранный язык(практ. зан) - 08.30 - 09.55 на БЛК, 5 каб. 305\nИностранный язык(практ. зан) - 10.05 - 11.30 на БЛК, 5 каб. 305\n\n<b>Пятница:</b>\nФизика(лекция) - 08.30 - 09.55 на Ожешко, 22 каб. 122\nИнформатика(лекция) - 10.05 - 11.30 на Ожешко, 22 каб. 122\nИнформатика(лекция) - 11.40 - 13.05 на Ожешко, 22 каб. 122\n", parse_mode="HTML")

async def start():

    print("Бот готов к работе")

    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    cursor.execute("SELECT subject, mark, date FROM grades WHERE user_id=624374169 AND subject='Математика'")
    # cursor.execute("INSERT INTO user_preferences(user_id) VALUES(?)", (tg_id))
    result = cursor.fetchall()
    print(result)
    # cursor.commit()
    cursor.close()

    # await bot.send_message(chat_id=624374169, text="", reply_markup=markup, parse_mode="HTML")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start())
