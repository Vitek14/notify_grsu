import grequests
import json
import sqlite3

def auth(user_id: int, login: str, password: str) -> dict | str:
    """Фукнция авторизует пользователя с помощью его логина и пароля. Функция возвращает либо текст с ошибкой для пользователя,
     либо словарь с данными аутентификации"""

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
        except IndexError:
            text = "Ошибка! Видимо ваши прекрасные ручки ошиблись и написали не тот логин или пароль. А может сайт решил прилечь на некоторое время... Мы не знаем!"
            return text


        main_auth_response = session.post("https://edu.grsu.by/auth/saml2/sp/saml2-acs.php/edu.grsu.by", data={
            "SAMLResponse": SAMLResponse,
            "RelayState": "https://edu.grsu.by/login/index.php"
        })

        cookies = session.cookies.get_dict()
        login_dict = {
            "username": login,
            "password": password,
            "MDL_SSP_AuthToken": cookies["MDL_SSP_AuthToken"],
            "MDL_SSP_SessID": cookies["MDL_SSP_SessID"],
            "MOODLEID1_": cookies["MOODLEID1_"],
            "MoodleSession": cookies["MoodleSession"]
        }
        return login_dict


# Переработать. Функция сделана из auth()
def get_user_info():
    return
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
    group_ids = [0, 0, 0, 0, 0, 0]
    for group in groups_info_json:
        current_group_id = group["GROUPINFO"]["K_SGRYP"]
        current_group_index = groups_info_json.index(group)
        for user in group["LIST"]:
            if TABNUM == user["TAB_NUM"]:  # Если студент и правда есть в этой группе, то выполняется это условие
                group_ids[current_group_index] = current_group_id
                print("Добавлена группа " + current_group_id)

    db_connection = sqlite3.connect("user.db", timeout=10.0)
    cursor = db_connection.cursor()


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
group_0=?,
group_1=?,
group_2=?,
group_3=?,
group_4=?,
group_5=?
WHERE tg_id=?""", (login, password, MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession, TABNUM, LANG, group_ids[0], group_ids[1], group_ids[2], group_ids[3], group_ids[4], group_ids[5], user_id,))
        
        
    else:
        cursor.execute("""INSERT INTO user_data
(username, password,
MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession,
tabnum, lang,
group_0, group_1, group_2, group_3, group_4, group_5,
tg_id) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?, ?)""", (login, password, MDL_SSP_AuthToken, MDL_SSP_SessID, MOODLEID1_, MoodleSession, TABNUM, LANG, group_ids[0], group_ids[1], group_ids[2], group_ids[3], group_ids[4], group_ids[5], user_id,))

    db_connection.commit()