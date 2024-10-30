import grequests
import json

import httpx
from aiohttp import ClientSession
from loguru import logger

from ..exceptions import InvalidCredentialsError, WebsiteConnectionError


class AboutMixin:
    @staticmethod
    async def async_auth(login: str, password: str, client: httpx.AsyncClient) -> dict:
        logger.info("Выполнение асинхронного входа")
        # Получаем токен
        logger.info("Отправление запроса GET на сайт с логином")
        before_auth_page = await client.get('https://edu.grsu.by/login', follow_redirects=True)
        if before_auth_page.status_code != 200:
            raise Exception(f"Failed to load login page, status code: {before_auth_page.status_code}")
        before_html = before_auth_page.text
        # cookies = session.cookie_jar.filter_cookies('https://edu.grsu.by')
        cookies = client.cookies
        logger.debug(f"Cookies: {cookies}")
        logger.debug(f"LOGIN WEB TEXT: {before_html}")
        authstate = before_html.split('name="AuthState" value="')[1].split('"')[0]

        data = {
            "username": login,
            "password": password,
            "AuthState": authstate
        }

        logger.info("Отправление запроса POST непосредственно на логин")
        response = await client.post('https://idp.grsu.by/simplesaml/module.php/core/loginuserpass.php', data=data,
                                     follow_redirects=True)
        # old_cookies = await session.cookies.get_dict()

        # Пытаемся найти значение токена пользователя, иначе возвращаем ошибку!
        try:
            samlresponse_raw = response.text
            samlresponse = samlresponse_raw.split('name="SAMLResponse" value="')[1].split('"')[0]
            logger.debug(f"SAML RESPONSE: {samlresponse}")
        except IndexError:
            raise InvalidCredentialsError

        # Логинимся, используя токен
        logger.info(f"Отправление запроса POST на логин используя токен")
        auth_result = await client.post("https://edu.grsu.by/auth/saml2/sp/saml2-acs.php/edu.grsu.by", data={
            "SAMLResponse": samlresponse,
            "RelayState": "https://edu.grsu.by/login/index.php"
        }, follow_redirects=True)

        logger.warning("Может возникнуть ошибка из-за того что куки получаются из запроса, а не сессии")
        # cookies = auth_result.cookies.get_dict()
        cookies = client.cookies
        logger.debug(f"COOKIES: {cookies}")
        # logger.debug(f"AUTH RESULT TEXT: {auth_result.text}")
        login_dict = {
            "MDL_SSP_AuthToken": cookies["MDL_SSP_AuthToken"],
            "MDL_SSP_SessID": cookies["MDL_SSP_SessID"],
            "MOODLEID1_": cookies["MOODLEID1_"],
            "MoodleSession": cookies["MoodleSession"],
        }
        return login_dict

    @staticmethod
    def auth(login: str, password: str) -> dict:
        """Функция авторизует пользователя с помощью его логина и пароля.
        :login: Логин пользователя на edu.grsu.by
        :password: Пароль пользователя на edu.grsu.by
        :return: Текст с ошибкой для пользователя, либо словарь с данными аутентификации
        """

        # Для автоматического закрытия сессии
        with grequests.Session() as session:

            # Получаем токен
            before_auth_page = session.get('https://edu.grsu.by/login')
            before_html = before_auth_page.text
            authstate = before_html.split('name="AuthState" value="')[1].split('"')[0]

            data = {
                "username": login,
                "password": password,
                "AuthState": authstate
            }

            response = session.post('https://idp.grsu.by/simplesaml/module.php/core/loginuserpass.php', data=data)
            old_cookies = session.cookies.get_dict()

            # Пытаемся найти значение токена пользователя, иначе возвращаем ошибку!
            try:
                samlresponse = response.text.split('name="SAMLResponse" value="')[1].split('"')[0]
            except IndexError:
                raise InvalidCredentialsError

            # Логинимся, используя токен
            session.post("https://edu.grsu.by/auth/saml2/sp/saml2-acs.php/edu.grsu.by", data={
                "SAMLResponse": samlresponse,
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

    @staticmethod
    def about(cookies: dict) -> dict:
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