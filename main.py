import grequests

import aiogram
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import asyncio

#fdfdfdfdfdf

# Импорт даты чтобы показывать расписание более приятным способом
from datetime import date, datetime, timedelta

import sqlite3

# Для нормальной обработки контента
import json

# Для чистки текста от html тегов
import re
CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

# Сессия requests
# session = grequests.Session()

# ПОМЕНЯТЬ!!!
tabnum = "170783"

def auth(user_id, login, password):

    # Для безопасного соединения, а также автоматического закрытия сессии
    with grequests.Session() as session:


        # Получаем токен для нормальной работы
        before_auth_page = session.get('https://edu.grsu.by/login')
        before_html = before_auth_page.text
        AuthState = before_html.split('name="AuthState" value="')[1].split('"')[0]

        data = {
            "username": login,
            "password": password,
            "AuthState": AuthState
        }

        response = session.post('https://idp.grsu.by/simplesaml/module.php/core/loginuserpass.php', data=data)

        # Пытаемся найти значение токена пользователя, иначе возвращаем ему ошибку!

        try:
            SAMLResponse = response.text.split('name="SAMLResponse" value="')[1].split('"')[0]
        except:
            text = "Ошибка! Видимо ваши прекрасные ручки ошиблись и написали не тот логин или пароль. А может сайт решил прилечь на некоторое время... Мы не знаем!"
            return text


        main_auth_response = session.post("https://edu.grsu.by/auth/saml2/sp/saml2-acs.php/edu.grsu.by", data={
            "SAMLResponse": SAMLResponse,
            "RelayState": "https://edu.grsu.by/login/index.php"
        })

        # all_courses_json = json.loads(main_auth_response.text)["1"]["1"]

        cookies = session.cookies.get_dict()

        MDL_SSP_AuthToken = cookies["MDL_SSP_AuthToken"]
        MDL_SSP_SessID = cookies["MDL_SSP_SessID"]
        MOODLEID1_ = cookies["MOODLEID1_"]
        MoodleSession = cookies["MoodleSession"]


        # Конец входа

        info_about_student = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getEmployeesData"
        })

        json_info = json.loads(info_about_student.text)

        useful_info = json_info["userInfo"]

        # Сохраняем tabnum и язык
        TABNUM = json_info["tabnum"]
        LANG = useful_info["LANG"]

        groups_info = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getGroups"
        })

        groups_info_json = json.loads(groups_info.text)

        # Прикол в том, что я не знаю есть ли и другие группы(количество)....

        # Ищем группу и добавляем туда пользователя
        group_ids = []
        for group in groups_info_json:
            current_group_id = group["GROUPINFO"]["K_SGRYP"]
            for user in group["LIST"]:
                # print(user["TAB_NUM"])
                if TABNUM == user["TAB_NUM"]:
                    group_ids.append(current_group_id)
                    print("Добавлена группа " + current_group_id)


        db_connection = sqlite3.connect("user.db", timeout=10.0)
        cursor = db_connection.cursor()

        print(MDL_SSP_AuthToken)
        print(MDL_SSP_SessID)
        print(MOODLEID1_)
        print(MoodleSession)
        print(TABNUM)
        print(LANG)
        print(group_ids[0])
        print(group_ids[1])
        print(group_ids[2])
        # print(group_ids[3])
        # print(type(user_id))

        cursor.execute("SELECT MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession FROM user_data WHERE tg_id=?", (user_id,))
        result = cursor.fetchone()
        if result:
            cursor.execute("""UPDATE user_data SET username=?,
password=?,
MDL_SSP_AuthToken=?,
MDL_SSP_SessID=?,
MOODLEID1_=?,
MoodleSession=?,
tabnum=?,
lang=?,
study_group=?,
lab_group_one=?,
faculty_group=?
WHERE tg_id=?""", (login, password, MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession, TABNUM, LANG, group_ids[0], group_ids[1], group_ids[2], group_ids[3], user_id))
        else:
            cursor.execute("INSERT INTO user_data VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (login, password, MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession, TABNUM, LANG, group_ids[0], group_ids[1], group_ids[2], user_id))

        db_connection.commit()


# lab_group_two=?,


bot = Bot("6315468656:AAElByUicc2WKyoydPfj1yvhsJfGhYAMrf4")

dp = Dispatcher()


@dp.message(Command("agree"))
async def agree_command(message):
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])



    btn1 = aiogram.types.InlineKeyboardButton(text="Я согласен", callback_data="Согласие")

    markup.inline_keyboard.append([btn1])

    await message.answer(text="Нажимая кнопку ниже, вы соглашаетесь с тем, что бот и разработчик смогут видеть, анализировать и использовать личные данные(логин, пароль, ваши данные об оценках, ваше имя, фамилия, отчество, а также другие данные)", protect_content=True, reply_markup=markup)


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


def select_auth_info(tg_id):
    # Подключаемся к базе данных с данными пользователя
    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    cursor.execute("SELECT username, password, MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession, tabnum FROM user_data WHERE tg_id=?", (tg_id,))
    result = cursor.fetchall()
    cursor.close()
    return result


def select_group_info(tg_id):
    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    cursor.execute("SELECT study_group, lab_group_one, lab_group_two, faculty_group FROM user_data WHERE tg_id=?", (tg_id,))
    result = cursor.fetchall()
    cursor.close()
    return result

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

@dp.message(Command("start"))
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

    group_info = select_group_info(callback_query.from_user.id)

    study_group = group_info[0][0]
    lab_group_one = group_info[0][1]
    lab_group_two = group_info[0][2]
    faculty_group = group_info[0][3]
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
            if (lesson["subgroup"]["id"] == lab_group_one) or (lesson["subgroup"]["id"] == lab_group_two) or (lesson["subgroup"]["id"] == faculty_group) or (lesson["subgroup"]["id"] == "0"):
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
    # bot = aiogram.Bot("6764455698:AAHWL7Zs60lWkqo8KdRcCfDs2yrd8YoxmEU")
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Подробнее", callback_data="Сегодня")
    btn2 = aiogram.types.InlineKeyboardButton(text="Оценки по этому предмету", callback_data="Завтра")

    markup.inline_keyboard.append([btn1, btn2])

    print("Бот готов к работе")

    # await bot.send_message(chat_id=624374169, text="", reply_markup=markup, parse_mode="HTML")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(start())
