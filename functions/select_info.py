import sqlite3
import grequests
import json

def select_auth_info(tg_id: int) -> list:
    """Получает данные о логине, пароле"""
    # Подключаемся к базе данных с данными пользователя
    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    cursor.execute("SELECT username, password, MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession, tabnum FROM user_data WHERE tg_id=?", (tg_id,))
    result = cursor.fetchall()
    cursor.close()
    return result


def select_group_info(tg_id: int) -> list:
    """Получает данные о группах студента"""
    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()

    # Получаем данные токена
    cursor.execute("SELECT group_0, group_1, group_2, group_3, group_4, group_5 FROM user_data WHERE tg_id=?", (tg_id,))
    result = cursor.fetchall()
    print(result)
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