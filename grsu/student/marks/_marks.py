import re
import grequests
import json
from sqlalchemy import select, delete, insert
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..data.select import get_marks
from ..data.delete import delete_marks
from ..data.insert import insert_new_marks

Base = declarative_base()

# Подключаемся к базе данных с данными пользователя
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)

# Объявляем объект сессии
Session = sessionmaker(engine)

CLEAN_TAGS = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')

def get_courses_data(self, user_id: int, cookies: dict):
    with grequests.Session() as session:
        all_courses = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
                "method": "getCoursesData"
            }, cookies=cookies)
        all_courses_json = json.loads(all_courses.text)["1"]["1"]
        return all_courses_json

def get_courses_names(self, all_courses: list) -> list:
    course_names = []
    for course in all_courses:
        name = course["course_name_ru"]
        course_names.append(name)
    return course_names

def get_marks_from_site(self, user_id: int, cookies: dict, student_info: dict, all_courses: list) -> list:
    """Функция отправляет запрос на сайт ГрГУ, чтобы получить необработанные данные об оценках"""
    tabnum = student_info["tabnum"]
        # Создание списка с запросами(requests) на каждый предмет, чтобы потом быстро получить данные о каждом
        # предмете на специальности
    requests = []

    for course in all_courses:
        course_id = course["kdisc"]

        MoodleSession = cookies["MoodleSession"]
        MDL_SSP_AuthToken = cookies["MDL_SSP_AuthToken"]
        MDL_SSP_SessID = cookies["MDL_SSP_AuthToken"]
        MOODLEID1_ = cookies["MOODLEID1_"]
        request = grequests.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getPerformanceData",
            "args[tabnum]": tabnum,
            "args[kdisc]": course_id,
            "args[semester]": "1",
            "args[year]": "2023",
            "args[lang]": "6"
        }, headers={
            "Connection": "keep-alive",
            "Cookies": f"MoodleSession={MoodleSession}; MDL_SSP_AuthToken={MDL_SSP_AuthToken}; "
                        f"MDL_SSP_SessID={MDL_SSP_SessID}, MOODLEID1_={MOODLEID1_} "
        })

        requests.append(request)

    responses = grequests.map(requests, stream=True)

    # Следующий код анализирует полученные ответы(responses) и добавляет в ЛИСТ КОРТЕЖИ из оценок с сайта
    marks_from_site = []
    for url in responses:
        subject_info = json.loads(url.text)

        # Проверяем существует ли предмет
        try:
            course_name = subject_info[0]["NDISC"]
        except Exception as error:
            continue

        # Проверяем каждое занятие на наличие оценки
        for lesson in subject_info:
            if lesson["SMARK"] == "":
                continue
                
            mark = lesson["SMARK"]
            date = lesson["DATE_ACADEMIC"]

            marks_from_site.append((mark, date, course_name, user_id))
        #     all_marks = all_marks + re.sub(CLEAN_TAGS, "",
        #                                 f'Оценка <b>{i["SMARK"]}</b> за {i["NPOCEN_KONTRL"]}.') + "\n"
        #     data.append((None, student_subject, i["SMARK"], i["DATE_ACADEMIC"], user_id))

        # text_marks = text_marks + f"Оценки по предмету {course_name}:\n{all_marks}\n\n"
    return marks_from_site

# def get_text_for_notification_marks(self, new_marks: set) -> str:
#     pass

# def get_text_for_marks(self, new_marks, all_marks):
#     text = "Оценки по предмету"
#     for 

def proccess_marks(self, user_id: int, responses: list, is_notification: bool):
    marks = get_marks(self, user_id)
    # if marks:
    #     # Удаляет оценки, чтобы можно было далее 
    #     delete_marks(self, user_id)
    # else:
    #     result = []

    new_marks = []

    # Текст, который отправится пользователю
    text_marks = ""
    data = []

    

    # Проверить позже
    new_marks = set(new_marks) - set(marks)



    # Если функция вызвана автоматически(для уведомлений)
    if is_notification:
        return new_marks

    insert_new_marks(self, user_id, data)

    if len(new_marks) != 0 and len(marks) != 0:
        text_marks = f"{text_marks}\n\nНОВОЕ:\n"
        for mark in new_marks:
            text_marks = text_marks + re.sub(CLEAN_TAGS, "", f"{mark[1]} по предмету {mark[0]} за {mark[2]}\n")

    return text_marks