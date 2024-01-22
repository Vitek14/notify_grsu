import grequests
import json
from ..exceptions import InvalidCredentialsError, ConnectionError

def auth(self, login: str, password: str) -> dict:
    """Фукнция авторизует пользователя с помощью его логина и пароля. Функция возвращает либо текст с ошибкой для пользователя,
     либо словарь с данными аутентификации"""

    # Для автоматического закрытия сессии
    with grequests.Session() as session:

        # Получаем токен
        before_auth_page = session.get('https://edu.grsu.by/login')
        before_html = before_auth_page.text
        AuthState = before_html.split('name="AuthState" value="')[1].split('"')[0]

        data = {
            "username": login,
            "password": password,
            "AuthState": AuthState
        }

        response = session.post('https://idp.grsu.by/simplesaml/module.php/core/loginuserpass.php', data=data)
        old_cookies = session.cookies.get_dict()

        # Пытаемся найти значение токена пользователя, иначе возвращаем ошибку!
        try:
            SAMLResponse = response.text.split('name="SAMLResponse" value="')[1].split('"')[0]
        except IndexError:
            raise InvalidCredentialsError

        # Логинимся, используя токен
        session.post("https://edu.grsu.by/auth/saml2/sp/saml2-acs.php/edu.grsu.by", data={
            "SAMLResponse": SAMLResponse,
            "RelayState": "https://edu.grsu.by/login/index.php"
        })

        cookies = session.cookies.get_dict()
        login_dict = {
            "MDL_SSP_AuthToken": cookies["MDL_SSP_AuthToken"],
            "MDL_SSP_SessID": cookies["MDL_SSP_SessID"],
            "MOODLEID1_": cookies["MOODLEID1_"],
            "MoodleSession": cookies["MoodleSession"],
        }
        return login_dict


# Переработать. Функция сделана из auth()
def about(self, cookies: dict) -> dict:
    with grequests.Session() as session:

        info_about_student = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getEmployeesData"
        }, cookies=cookies)

        json_info = json.loads(info_about_student.text)
        useful_info = json_info["userInfo"]

        # Сохраняем tabnum и язык
        TABNUM = json_info["tabnum"]
        LANG = useful_info["LANG"]

        groups_info = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getGroups"
        }, cookies=cookies)

        cookies["tabnum"] = TABNUM
        cookies["lang"] = LANG

        groups_info_json = json.loads(groups_info.text)

        # Ищем группу и добавляем туда пользователя
        group_ids = [0, 0, 0, 0, 0, 0]
        for group in groups_info_json:
            current_group_id = group["GROUPINFO"]["K_SGRYP"]
            current_group_index = groups_info_json.index(group)
            for user in group["LIST"]:
                if TABNUM == user["TAB_NUM"]:  # Если студент и правда есть в этой группе, то выполняется это условие
                    group_ids[current_group_index] = current_group_id
                    name = f"group_{current_group_index}"
                    cookies[name] = current_group_id
        return cookies