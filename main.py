# -*- coding: utf-8 -*-
import asyncio
import locale
# Для нормальной обработки контента
# Для чистки текста от html тегов
import re
from datetime import datetime
# Импорт даты, чтобы показывать расписание более приятным способом
from datetime import timedelta

# Импорт функций
from functions.auth import auth
from functions.select_info import select_auth_info, get_attestation
from grsu.exceptions import *
from grsu.schedule import Schedule          # Отвечает за расписание
from grsu.student import Student            # Отвечает за все методы, связанные со студентом
from grsu.student.marks import Marks        # Отвечает за оценки студента
from grsu.student.settings import Settings  # Отвечает за настройки пользователя

import aiogram
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import BufferedInputFile
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from settings import API_KEY
from settings import settings_dict, settings_buttons

import platform

# Устанавливаем русскую локализацию
if platform.system() == "Windows":
    locale.setlocale(locale.LC_TIME, 'ru_RU')
else:
    locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

CLEAN_TAGS = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

bot = Bot(API_KEY)

student = Student()
st_marks = Marks()
schedule = Schedule()
st_settings = Settings()
form_router = Router()

dp = Dispatcher()
scheduler = AsyncIOScheduler()


class StateMarks(StatesGroup):
    subject = State()


class StateSettings(StatesGroup):
    previous_message = State()
    text = State()
    buttons = State()
    category = State()
    settings = State()


class StateSchedule(StatesGroup):
    day = State()


def clear_state(func):
    async def wrapper(message, state: FSMContext):
        clear = await message.answer(text="Удаляем лишние кнопки, если имеются...", protect_content=True,
                                     reply_markup=ReplyKeyboardRemove())
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
async def settings_command(message, state):
    user_id = message.from_user.id
    user_settings = st_settings.get_settings(user_id)
    if len(user_settings) == 0:
        st_settings.create_settings(user_id)
        user_settings = st_settings.get_settings(user_id)

    keyboard_list = [[KeyboardButton(text="Инфо")], [KeyboardButton(text="Уведомления")],
                     [KeyboardButton(text="Логин")], [KeyboardButton(text="Расписание")],
                     [KeyboardButton(text="Убрать это...")]]

    buttons = ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)

    await message.answer(f"""Это меню настроек. Ниже выберите категорию настроек и настройте что вы хотите.""",
                         reply_markup=buttons)
    await state.set_state(StateSettings.category)


@dp.message(StateSettings.category)
async def settings_reply(message, state: FSMContext) -> None:
    if message.text == "Убрать это...":
        await state.clear()
        await message.answer(text="Хорошо, убрали кнопки для вас!", reply_markup=ReplyKeyboardRemove())
        return
    # print(message.text)
    try:
        keyboard_list = settings_buttons[message.text]  # Ищем настройку по названию
    except KeyError:
        await message.answer("Неверная настройка")
        return
    buttons = ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)
    user_id = message.from_user.id
    user_settings = st_settings.get_settings(user_id)
    text = ""

    # Перебор значений в словаре, который содержит начальный текст и названий настроек из базы данных(их
    # сопоставление с простым русским языком)
    for item, value in settings_dict[message.text].items():
        if item == "text":
            text = str(text) + str(value)
            continue
        text = text + "\n" + item + ": " + str(user_settings[value])
    bot_message = await message.answer(text, reply_markup=buttons)
    await state.update_data(previous_message=bot_message)
    await state.update_data(text=message.text)
    await state.set_state(StateSettings.settings)


@dp.message(StateSettings.settings)
async def info_settings_reply(message, state: FSMContext) -> None:
    if message.text == "Убрать это...":
        await state.clear()
        await message.answer(text="Хорошо, убрали кнопки для вас!", reply_markup=ReplyKeyboardRemove())
        return
    if message.text == "Назад":
        await state.clear()
        await settings_command(message, state)
        return
    previous_data = await state.get_data()
    user_id = message.from_user.id

    try:
        setting_name = str(settings_dict[previous_data["text"]][message.text])
    except KeyError:
        await message.answer(text="Неверная настройка")
        return

    settings = st_settings.get_settings(user_id)
    value = settings[setting_name]
    value ^= 1
    st_settings.update_setting(user_id, setting_name, value)
    keyboard_list = settings_buttons[previous_data["text"]]
    buttons = ReplyKeyboardMarkup(keyboard=keyboard_list, resize_keyboard=True)
    user_settings = st_settings.get_settings(user_id)

    text = ""
    for item, value in settings_dict[previous_data["text"]].items():
        if item == "text":
            text = str(text) + str(value)
            continue
        text = text + "\n" + item + ": " + str(user_settings[value])
    bot_message = await message.answer(text, reply_markup=buttons)
    await previous_data["previous_message"].delete()
    await message.delete()
    await state.update_data(previous_message=bot_message)


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
        # login_info = student.get_login(user_id)
        # new_token = student.auth(login_info["username"], login_info["password"])
        # student.refresh_token(new_token, user_id)
        # about_info = student.get_about(new_token)

        about_info["userInfo"]
    except Exception as error:
        await bot_message.edit_text("Видимо токен устарел, пробуем обновить...")

        # TODO: Нужно поменять функцию get_login и auth
        login_info = student.get_login(user_id)
        new_token = student.auth(login_info["username"], login_info["password"])

        student.refresh_token(new_token, user_id)
        about_info = student.get_about(new_token)  # TODO: Поменять функцию get_about, чтобы не было self

    useful_info = about_info["userInfo"]
    markup = aiogram.types.InlineKeyboardMarkup(inline_keyboard=[])

    btn1 = aiogram.types.InlineKeyboardButton(text="Оценки", callback_data="Оценки")
    btn2 = aiogram.types.InlineKeyboardButton(text="Расписание", callback_data="Расписание")

    markup.inline_keyboard.append([btn1, btn2])

    user_settings = st_settings.get_settings(user_id)

    # В зависимости от настроек из базы данных либо добавлять, либо НЕ добавлять в сообщение
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
    await callback_query.answer(text="Производим запросы, это занимает обычно 5 секунд...",
                                reply_markup=ReplyKeyboardRemove())

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

    await callback_query.message.answer("Выберите желаемый предмет",
                                        reply_markup=buttons)  # Узнать проблему с жирным шрифтом
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
        await message.answer(
            text="Мы не нашли оценок для этого предмета, попробуйте другой или уберите эти кнопки снизу нажав на соответствующую кнопку")
        return

    await message.answer(text=text, parse_mode="HTML")


@dp.callback_query(F.data == "Расписание")
async def schedule_button(callback_query, state: FSMContext):
    # await callback_query.answer(text="Производим запросы...")
    data = await state.get_data()
    try:
        current_day = data["day"]
    except KeyError:
        current_day = datetime.today()
    user_id = callback_query.from_user.id
    group_info = student.get_groups(user_id)

    study_group = group_info["group_0"]
    lab_groups = [group_info["group_1"], group_info["group_2"], group_info["group_3"],
                  group_info["group_4"], group_info["group_5"]]

    if not schedule.if_exists(study_group):
        schedule.create_schedule(study_group)

    schedule_db = schedule.get_student_schedule_from_db(study_group)
    # user_settings = st_settings.get_settings(user_id)
    today = current_day.strftime("%Y-%m-%d")
    student_tuple = (study_group, *lab_groups, user_id, today)
    student_groups = [student_tuple]
    all_raw_lessons = schedule.get_schedule_text(schedule_db, student_groups, False)
    all_lessons = all_raw_lessons[0]["text"]
    print(all_raw_lessons)
    schedule_photo = schedule.get_schedule_photo(student_tuple, schedule_db, all_raw_lessons[0]["real_lessons"])

    text_lessons = ""
    # Отображение как "среда, 14 фев."
    day_text = current_day.strftime("%A, %d %b:\n")

    buttons = [[KeyboardButton(text="Предыдущий день")], [KeyboardButton(text="Сегодня")],
               [KeyboardButton(text="Следующий день")], [KeyboardButton(text="Убрать это...")]]
    keyboard = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

    # Если нет уроков, то студент свободен
    if len(all_lessons) == 0:
        all_lessons = "Спать: 00:00-23:59"

    # Загружаем изображение на сервера телеграмм
    telegram_photo = BufferedInputFile(schedule_photo.read(), filename="schedule.png")
    # print(schedule_photo)
    # В зависимости от того, как вызвана функция, выполнять разные действия
    if str(type(callback_query)) == "<class 'aiogram.types.callback_query.CallbackQuery'>":
        await callback_query.message.answer(text=day_text + all_lessons, reply_markup=keyboard, parse_mode="HTML")
        await bot.send_photo(chat_id=user_id, photo=telegram_photo, reply_markup=keyboard, parse_mode="HTML")
    else:
        await bot.send_message(chat_id=user_id, text=day_text + all_lessons, reply_markup=keyboard, parse_mode="HTML")
        await bot.send_photo(chat_id=user_id, photo=telegram_photo, reply_markup=keyboard, parse_mode="HTML")
    # Выставить FSM и данные о текущем ВЫБРАННОМ дне
    await state.set_state(StateSchedule.day)
    await state.update_data(day=current_day)


@dp.message(StateSchedule.day)
async def schedule_selected(message, state: FSMContext) -> None:
    if message.text == "Убрать это...":
        await state.clear()
        await message.answer(text="Хорошо, убрали кнопки для вас!", reply_markup=ReplyKeyboardRemove())
        return
    if message.text == "Следующий день":
        previous_day = await state.get_data()
        await state.update_data(day=previous_day["day"] + timedelta(1))
        await schedule_button(message, state)
    if message.text == "Предыдущий день":
        previous_day = await state.get_data()
        await state.update_data(day=previous_day["day"] - timedelta(1))
        await schedule_button(message, state)
    if message.text == "Сегодня":
        previous_day = await state.get_data()
        await state.update_data(day=datetime.today())
        await schedule_button(message, state)


async def start():
    print("Бот готов к работе")
    job = scheduler.add_job(schedule.notify, "interval", minutes=2, args=[bot])
    scheduler.start()
    # job.
    # asyncio.create_task(timer(bot, 300))
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(start())
