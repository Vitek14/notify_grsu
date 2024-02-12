# -*- coding: utf-8 -*-
import grequests
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, reply_keyboard_markup
import asyncio
# Для нормальной обработки контента
import json
# Для чистки текста от html тегов
import re
# Импорт даты, чтобы показывать расписание более приятным способом
from datetime import datetime, timedelta

import aiogram
from aiogram import Bot, Dispatcher, Router, F, types
from aiogram.filters.command import Command
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext

# Импорт функций
from functions.auth import auth
from functions.notifications import timer
from functions.select_info import select_auth_info, select_group_info, get_web_user_info, get_attestation
from settings import API_KEY
from aiogram.fsm.state import State, StatesGroup

from grsu.student import Student
from grsu.student.marks import Marks
from grsu.student.settings import Settings
from grsu.schedule import Schedule
from grsu.exceptions import *

from settings import info_settings

from datetime import datetime
import locale

# Устанавливаем русскую локализацию
locale.setlocale(locale.LC_TIME, 'ru')

CLEAN_TAGS = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

bot = Bot(API_KEY)

student = Student()
st_marks = Marks()
schedule = Schedule()
st_settings = Settings()
form_router = Router()

dp = Dispatcher()

class StateMarks(StatesGroup):
    subject = State()

class StateSettings(StatesGroup):
    previous_message = State()
    category = State()
    settings = State()

def clear_state(func):
    async def wrapper(message, state: FSMContext):
        clear = await message.answer(text="Удаляем лишние кнопки, если имеются...", protect_content=True, reply_markup=ReplyKeyboardRemove())
        await clear.delete()
        await state.clear()
        original_func = await func(message, state)
        return original_func
    return wrapper


@dp.message(Command("agree"))
@clear_state
async def agree_command(message):
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Я согласен", callback_data="Согласие")

    markup.inline_keyboard.append([btn1])

    await message.answer(text="Нажимая кнопку ниже, вы соглашаетесь с тем, что бот и разработчик смогут видеть, "
                              "анализировать и использовать личные данные(логин, пароль, ваши данные об оценках, "
                              "ваше имя, фамилия, отчество, а также другие личные данные)", protect_content=True,
                         reply_markup=markup)


def set_default_preferences(tg_id):
    # Подключаемся к базе данных с данными пользователя
    pass


@dp.message(Command("login"))
@clear_state
async def login_command(message, state):
    text = message.text.split(" ")
    if len(text) < 3 or len(text) > 3:
        await message.answer(text="Неправильно введены данные!")
        return
    login = text[1]
    password = text[2]

    user_id = message.from_user.id
    await message.delete()
    waiting_message = await bot.send_message(chat_id=message.from_user.id,
                                             text="Пробуем войти, это может занять некоторое время ⌛️")

    # Функция входа
    try:
        auth_info = student.auth(login, password)
    except InvalidCredentialsError:
        await waiting_message.edit_text(text=InvalidCredentialsError().message)
        return

    if not student.check_if_exists(user_id):
        student.create_new_student(user_id, auth_info, login, password)

    # Создание настроек пользователя, если не созданы
    user_settings = st_settings.get_settings(user_id)
    if len(user_settings) == 0:
        st_settings.create_settings(user_id)

    await waiting_message.edit_text(
        text="Вы это сделали! Теперь вы авторизованы в боте. Учтите, что вы всегда можете удалить ваши данные с "
             "помощью /delete")


@dp.message(Command("attestation"))
@clear_state
async def attestation(message):
    bot_message = await message.answer(text="Производим запросы...", protect_content=True)

    # Есть повторение в коде. Повторяется, где настройки
    result = select_auth_info(message.from_user.id)

    if not result:
        await bot_message.edit_text("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return

    info = get_attestation(result)
    print(info)

    await bot_message.edit_text("Видимо токен устарел, пробуем обновить...")
    auth(message.from_user.id, result[0][0], result[0][1])
    result = select_auth_info(message.from_user.id)
    info = get_attestation(result)

    # useful_info = info["userInfo"]
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Успеваемость", callback_data="Успеваемость")
    # btn2 = aiogram.types.InlineKeyboardButton(text="Расписание", callback_data="Расписание")

    markup.inline_keyboard.append([btn1])

    await bot_message.edit_text(f"""Тест""", reply_markup=markup, protect_content=True)


@dp.message(Command("settings"))
async def settings(message, state):
    # bot_message = await message.answer("Получаем ваши настройки...")
    user_id = message.from_user.id
    user_settings = st_settings.get_settings(user_id)
    if len(user_settings) == 0:
        st_settings.create_settings(user_id)
        user_settings = st_settings.get_settings(user_id)
    
    keyboard_list = [[KeyboardButton(text="Инфо")], [KeyboardButton(text="Уведомления")], [KeyboardButton(text="Логин")], [KeyboardButton(text="Убрать это...")]]

    buttons = ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)

    await message.answer(f"""Это меню настроек. Ниже выберите категорию настроек и настройте что вы хотите.""", reply_markup=buttons)
    await state.set_state(StateSettings.category)

@dp.message(StateSettings.category)
@form_router.message(F.text.casefold() == "Инфо")
async def settings_reply(message, state: FSMContext) -> None:
    # if message.text == "Убрать это...":
    #     await state.clear()
    #     await message.answer(text="Хорошо, убрали кнопки для вас!", reply_markup=ReplyKeyboardRemove())
    #     return
    keyboard_list = [[KeyboardButton(text="Показывать факультет"), KeyboardButton(text="Показывать специальность")], [KeyboardButton(text="Показывать почту"), KeyboardButton(text="Показывать группу")], [KeyboardButton(text="Убрать это...")]]

    buttons = ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)
    user_id = message.from_user.id
    user_settings = st_settings.get_settings(user_id)
    bot_message = await message.answer(f"""Следующие настройки затрагивают команду /info:
Показывать факультет: {user_settings["show_faculty"]}
Показывать специальность: {user_settings["show_specialization"]}
Показывать почту: {user_settings["show_email"]}
Показывать группу: {user_settings["show_group"]}""", reply_markup=buttons)
    await state.update_data(previous_message=bot_message)
    await state.set_state(StateSettings.settings)


@dp.message(StateSettings.settings)
async def info_settings_reply(message, state: FSMContext) -> None:
    if message.text == "Убрать это...":
        await state.clear()
        await message.answer(text="Хорошо, убрали кнопки для вас!", reply_markup=ReplyKeyboardRemove())
        return
    previous_message = await state.get_data()
    # print(previous_message)
    # print(previous_message["previous_message"].text)
    user_id = message.from_user.id

    if message.text in info_settings:
        settings = st_settings.get_settings(user_id)
        value = settings[info_settings[message.text]]
        value ^= 1
        st_settings.update_setting(user_id, info_settings[message.text], value)
        keyboard_list = [[KeyboardButton(text="Показывать факультет"), KeyboardButton(text="Показывать специальность")], [KeyboardButton(text="Показывать почту"), KeyboardButton(text="Показывать группу")], [KeyboardButton(text="Убрать это...")]]
        buttons = ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)
        user_settings = st_settings.get_settings(user_id)
        bot_message = await message.answer(f"""Следующие настройки затрагивают команду /info:
Показывать факультет: {user_settings["show_faculty"]}
Показывать специальность: {user_settings["show_specialization"]}
Показывать почту: {user_settings["show_email"]}
Показывать группу: {user_settings["show_group"]}""", reply_markup=buttons)
        await previous_message["previous_message"].delete()
        await message.delete()
        await state.update_data(previous_message=bot_message)
    # marks = st_marks.get_marks(user_id)

@dp.message(Command("info"))
@clear_state
async def start_command(message, state):
    
    bot_message = await message.answer(text="Производим запросы...", protect_content=True)

    user_id = message.from_user.id
    result = student.check_if_exists(user_id)

    if not result:
        await bot_message.edit_text("Вы ещё не вошли в аккаунт! Сделайте это с помощью команды /login")
        return

    token_info = student.get_token(user_id)
    print("Token is")
    print(token_info)
    about_info = student.get_about(token_info)

    try:
        # САЙТ ИЗМЕНИЛИ В ХУДШУЮ СТОРОНУ! СЛЕДУЮЩИХ СТРОК НЕ ДОЛЖНО БЫЛО БЫТЬ!!
        login_info = student.get_login(user_id)
        new_token = student.auth(login_info["username"], login_info["password"])
        student.refresh_token(new_token, user_id)
        about_info = student.get_about(new_token)


        about_info["userInfo"]
    except Exception as error:
        await bot_message.edit_text("Видимо токен устарел, пробуем обновить...")
        login_info = student.get_login(user_id)
        new_token = student.auth(login_info["username"], login_info["password"])
        student.refresh_token(new_token, user_id)
        about_info = student.get_about(new_token)


    useful_info = about_info["userInfo"]
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Оценки", callback_data="Оценки")
    btn2 = aiogram.types.InlineKeyboardButton(text="Расписание", callback_data="Расписание")

    markup.inline_keyboard.append([btn1, btn2])

    user_settings = st_settings.get_settings(user_id)
    faculty = ("\nФакультет: " + useful_info["N_OTDEL"]) if user_settings["show_faculty"] == 1 else ""
    specialization = ("\nСпециальность: " + useful_info["NNAUCH"]) if user_settings["show_specialization"] == 1 else ""
    email = ("\nEMAIL: " + useful_info["EMAIL"]) if user_settings["show_email"] == 1 else ""
    group = ("\nГруппа: " + useful_info["N_GRYP"]) if user_settings["show_group"] == 1 else ""


    await bot_message.edit_text(f"""
ФИО: {useful_info["FIO_R"]}
Курс: {useful_info["N_D"]}{faculty}{specialization}{email}{group}""",
reply_markup=markup, protect_content=True)


@dp.callback_query(F.data == "Оценки")
async def user_marks(callback_query, state: FSMContext):
    await callback_query.answer(text="Производим запросы, это занимает обычно 5 секунд...", reply_markup=ReplyKeyboardRemove())

    user_id = callback_query.from_user.id
    user_auth_info = student.get_token(user_id)
    about_info = student.get_about(user_auth_info)

    courses_data = st_marks.get_courses_data(user_id, user_auth_info)
    course_names = st_marks.get_courses_names(courses_data)
    marks = st_marks.get_marks_from_site(user_id, user_auth_info, about_info, courses_data)
    db_marks = st_marks.get_marks(user_id)

    # Изменить
    new_marks = set(db_marks) - set(marks)
    deleted_marks = set(marks) - set(marks)

    print(new_marks)
    print(deleted_marks)

    if len(new_marks) != 0:
        st_marks.insert_new_marks(user_id, list(deleted_marks))
    if len(deleted_marks) != 0:
        st_marks.delete_marks(user_id, list(new_marks))

    keyboard_list = []
    sort_list = []
    for subject in course_names:
        if len(sort_list) == 2 or len(course_names) == course_names.index(subject):
            keyboard_list.append(sort_list)
            sort_list = []
        sort_list.append(KeyboardButton(text=subject))
    keyboard_list.append([KeyboardButton(text="Убрать это...")])

    buttons = ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)

    await callback_query.message.answer("Выберите желаемый предмет", reply_markup=buttons)  # Узнать проблему с жирным шрифтом
    await state.set_state(StateMarks.subject)

@dp.message(StateMarks.subject)
async def process_name(message, state: FSMContext) -> None:
    if message.text == "Убрать это...":
        await state.clear()
        await message.answer(text="Хорошо, убрали кнопки для вас!", reply_markup=ReplyKeyboardRemove())
        return

    user_id = message.from_user.id
    marks = st_marks.get_marks(user_id)
    text = "Оценки по предмету " + message.text + ":\n"
    subject_list = []
    for mark in marks:
        if message.text in mark:
            date_obj = datetime.strptime(mark[2], "%Y-%m-%d %H:%M:%S")
            # Форматируем дату с использованием локализации
            formatted_date = date_obj.strftime("%A, %d %B, %H:%M")
            text = text + "<b>" + re.sub(CLEAN_TAGS, "", mark[1]) + "</b> за " + formatted_date + "\n"
            subject_list.append(mark)

    if len(subject_list) == 0:
        await message.answer(text="Мы не нашли оценок для этого предмета, попробуйте другой или уберите эти кнопки снизу нажав на соответствующую кнопку")
        return

    await message.answer(text=text, parse_mode="HTML")


@dp.callback_query(F.data == "Расписание")
async def marks(callback_query):
    await callback_query.answer(text="Производим запросы...")

    group_info = select_group_info(callback_query.from_user.id)

    study_group = group_info[0][0]
    print("Study is " + type(study_group))
    lab_group_one = group_info[0][1]
    lab_group_two = group_info[0][2]
    lab_group_three = group_info[0][3]
    lab_group_four = group_info[0][4]
    faculty_group = group_info[0][5]

    if not schedule.if_exists(study_group):
        schedule.create_schedule(study_group)

    # raw_schedule = schedule.get_raw_schedule(study_group)
    # group_schedule = schedule.process_schedule(raw_schedule, study_group)
    with grequests.Session() as session:
        group_schedule = session.get(f"https://api.grsu.by/1.x/app1/getGroupSchedule?groupId={study_group}")
    json_group_schedule = json.loads(group_schedule.text)
    db_schedule = schedule.get_schedule_from_db(study_group)
    

    today_raw = datetime.today()  # .strftime('%Y-%m-%d')
    yesterday_raw = today_raw - timedelta(1)
    tomorrow_raw = today_raw + timedelta(1)

    today = today_raw.strftime('%Y-%m-%d')
    yesterday = yesterday_raw.strftime('%Y-%m-%d')
    tomorrow = tomorrow_raw.strftime('%Y-%m-%d')

    text_lessons = ""
    today_lessons = ""
    tomorrow_lessons = ""
    # date_counter = 0
    for item in json_group_schedule["days"]:
        print(item["date"])
        if item["date"] == today:
            # text_lessons = text_lessons + "\n\n" + "СЕГОДНЯ" + "\n"
            today_lessons = today_lessons + "\n\n" + "СЕГОДНЯ" + "\n"
            date_counter = 2
        elif item["date"] == yesterday:
            text_lessons = text_lessons + "\n\n" + "Вчера" + "\n"
            date_counter = 1
        elif item["date"] == tomorrow:
            # text_lessons = text_lessons + "\n\n" + "Завтра" + "\n"
            tomorrow_lessons = tomorrow_lessons + "\n\n" + "Завтра" + "\n"
            date_counter = 3
        else:
            text_lessons = text_lessons + "\n\n" + item["date"] + "\n"
            date_counter = 0

        # Перебор для уроков
        for lesson in item["lessons"]:
            if (lesson["subgroup"]["id"] == lab_group_one) or (lesson["subgroup"]["id"] == lab_group_two) or (
                    lesson["subgroup"]["id"] == lab_group_three) or (lesson["subgroup"]["id"] == lab_group_four) or (
                    lesson["subgroup"]["id"] == faculty_group) or (lesson["subgroup"]["id"] == "0"):
                if date_counter == 2:
                    today_lessons = today_lessons + f"{lesson['title']} ({lesson['timeStart']} - " \
                                                    f"{lesson['timeEnd']}) - {lesson['address']}\n "
                elif date_counter == 3:
                    tomorrow_lessons = tomorrow_lessons + f"{lesson['title']} ({lesson['timeStart']} - " \
                                                          f"{lesson['timeEnd']}) - {lesson['address']}\n "
                else:
                    text_lessons = text_lessons + f"{lesson['title']} ({lesson['timeStart']} - " \
                                                  f"{lesson['timeEnd']}) - {lesson['address']}\n"
            else:
                continue

    await callback_query.message.answer(f"{text_lessons}\n{tomorrow_lessons}\n{today_lessons}")


async def start():
    print("Бот готов к работе")
    # asyncio.create_task(timer(bot, 300))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start())
