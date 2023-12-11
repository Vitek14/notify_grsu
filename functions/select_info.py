import sqlite3

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
    cursor.execute("SELECT group_0, group_1, group_2, group_3, group_4, group_5 FROM user_data WHERE tg_id=?", (tg_id,))
    result = cursor.fetchall()
    cursor.close()
    return result