import json
import re
import sqlite3
from typing import Union, Any

import grequests

CLEAN_TAGS = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')


async def get_raw_marks(user_auth_info: list) -> list:
    """Функция отправляет запрос на сайт ГрГУ, чтобы получить необработанные данные об оценках"""

    # Переменные, полученные из базы данных
    MDL_SSP_AuthToken = user_auth_info[0][2],
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

        # Текст, который будет отправляться пользователю в тг
        requests = []

        # Создание списка с запросами(requests) на каждый предмет, чтобы потом быстро получить данные о каждом
        # предмете на специальности
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
                "Connection": "keep-alive",
                "Cookies": f"MoodleSession={MoodleSession}; MDL_SSP_AuthToken={MDL_SSP_AuthToken}; "
                           f"MDL_SSP_SessID={MDL_SSP_SessID}, MOODLEID1_={MOODLEID1_} "
            })

            requests.append(request)

        responses = grequests.map(requests, stream=True)
        print("Type")
        print(type(responses))
        return responses


# def 


def proccess_marks(user_id: int, responses: list, is_notification: bool) -> \
        Union[Union[set[tuple[Any, Any, Any]], str], Any]:
    db = sqlite3.connect("user.db")
    cursor = db.cursor()

    cursor.execute("SELECT subject, mark, date FROM grades WHERE user_id=?", (user_id,))
    result = cursor.fetchall()
    if result != 0:
        cursor.execute("DELETE FROM grades WHERE user_id=?", (user_id,))

    marks = []
    text_marks = ""
    for item in responses:
        json_course = json.loads(item.text)

        all_marks = ""
        # student_marks = []  # Аналог all_marks, потом надо убрать all_marks, если с student_marks будет нормально
        # работать

        student_marks = []
        student_marks_dates = []

        # Проверяем даёт ли запрос на название предмета ответ
        try:
            course_name = json_course[0]["NDISC"]  # Убрать
            student_subject = json_course[0]["NDISC"]
        except Exception as error:
            print(error)
            continue

        for i in json_course:
            if i["SMARK"] == "":
                continue
            student_marks.append(i["SMARK"])
            student_marks_dates.append(i["DATE_ACADEMIC"])
            marks.append((course_name, i["SMARK"], i["DATE_ACADEMIC"]))
            all_marks = all_marks + re.sub(CLEAN_TAGS, "",
                                           f'Оценка <b>{i["SMARK"]}</b> за {i["NPOCEN_KONTRL"]}.') + "\n"

        data = [(student_subject, student_marks[i], student_marks_dates[i], user_id) for i in range(len(student_marks))]
        # вставляем все данные об оценках в таблицу grades одним запросом

        cursor.executemany("INSERT INTO grades (subject, mark, date, user_id) VALUES (?, ?, ?, ?)", data)
        # cursor.executemany("INSERT INTO grades marks VALUES (?)", data)

        text_marks = text_marks + f"Оценки по предмету {course_name}:\n{all_marks}\n\n"

    db.commit()
    db.close()

    new_marks = set(marks) - set(result)

    # Если функция вызвана автоматически(для уведомлений)
    if is_notification:
        return new_marks

    if len(new_marks) != 0:
        text_marks = f"{text_marks}\n\nНОВОЕ:\n"
        for mark in new_marks:
            text_marks = text_marks + mark[1] + " по предмету " + mark[0] + " за " + mark[2] + "\n"

    return text_marks
