import grequests
import json

from aiohttp import ClientSession
from loguru import logger
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from settings import base_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import re

Base = declarative_base()

# Подключаемся к базе данных с данными пользователя
engine = create_engine(base_engine)
Base.metadata.create_all(engine)


class ParseMixin:
    """
    Класс обёртка
    """

    @staticmethod
    async def async_get_about(token_info: dict, session: ClientSession) -> dict:
        """
        Получение базовых данных о студенте, включая его ФИО, курс и т.д в асинхронном режиме.
        :param session: Сессия aiohttp.
        :param token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие.
        :return:
        """
        # async with session:
        async with session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getEmployeesData"
        }, cookies=token_info) as info_about_student:
            logger.debug(f"Код employees_data: {info_about_student.status}")
            if info_about_student.status != 200:
                logger.warning(f"https://edu.grsu.by/custom-components/custom-api/ajax-router.php выдала код "
                               f"{info_about_student.status}")
            text = await info_about_student.text()
            info = json.loads(text)
        return info

    @staticmethod
    async def get_skips(token_info: dict, session: ClientSession) -> list[dict]:
        """
        Получение пропусков студента в асинхронном режиме.
        :param session: Сессия aiohttp.
        :param token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие.
        :return: Лист из словарей с информацией о пропусках
        """
        async with session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getSkips",
            "args": "production"
        }, cookies=token_info) as skips_info:
            text = await skips_info.text()
            info = json.loads(text)
            logger.debug(f"SKIPS_INFO: {skips_info}")
        return info

    @staticmethod
    async def get_attestation(token_info: dict, session: ClientSession) -> list[dict]:
        """
        Получение промежуточной аттестации студента в асинхронном режиме.
        :param session: Сессия aiohttp.
        :param token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие.
        :return: Лист из словарей с информацией о промежуточной аттестацией
        """
        async with session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getAttestation"
        }, cookies=token_info) as attestation_request:
            text = await attestation_request.text()
            attestation_info = json.loads(text)
            logger.debug(f"ATTESTATION INFO: {attestation_info}")
        return attestation_info

    @staticmethod
    async def get_exams(token_info: dict, session: ClientSession) -> list[dict]:
        """
        Получение промежуточной аттестации студента в асинхронном режиме.
        :param session: Сессия aiohttp.
        :param token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие.
        :return: Лист из словарей с информацией об экзаменах
        """
        async with session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getProgress",
            "args": "production"
        }, cookies=token_info) as exams_request:
            text = await exams_request.text()
            exams_info = json.loads(text)
            logger.debug(f"EXAMS INFO: {exams_info}")
        return exams_info

    @staticmethod
    def get_about(token_info: dict) -> dict:
        """
        Получение базовых данных о студенте, включая его имя, курс и т.д

        :token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие
        """
        with grequests.Session() as session:
            info_about_student = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
                "method": "getEmployeesData"
            }, cookies=token_info)
            logger.debug(f"Код employees_data: {info_about_student.status_code}")
            if info_about_student.status_code != 200:
                logger.warning(f"https://edu.grsu.by/custom-components/custom-api/ajax-router.php выдала код "
                               f"{info_about_student.status_code}")
            info = json.loads(info_about_student.text)
        return info

    @staticmethod
    def get_attestation(token_info: dict) -> dict:
        """
        Получение данных о промежуточной аттестации студента

        :token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие
        """
        with grequests.Session() as session:
            raw_attestation_info = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
                "method": "getAttestation"
            }, cookies=token_info)
            attestation_info = json.loads(raw_attestation_info.text)
        return attestation_info
