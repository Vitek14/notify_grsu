import grequests
import json

import httpx
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
    async def async_get_skips(token_info: dict, client: httpx.AsyncClient) -> list[dict]:
        """
        Получение пропусков студента в асинхронном режиме.
        :param client: Асинхронный клиент httpx.
        :param token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие.
        :return: Лист из словарей с информацией о пропусках
        """
        skips_request = await client.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getSkips",
            "args": "production"
        }, cookies=token_info)
        text = skips_request.text
        skips = json.loads(text)
        logger.debug(f"SKIPS_INFO: {skips}")
        return skips

    @staticmethod
    async def async_get_attestation(token_info: dict, client: httpx.AsyncClient) -> list[dict]:
        """
        Получение промежуточной аттестации студента в асинхронном режиме.
        :param client: Клиент httpx.
        :param token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие.
        :return: Лист из словарей с информацией о промежуточной аттестацией
        """
        logger.info("Отправление запроса на промежуточную аттестацию")
        attestation_request = await client.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getAttestation"
        }, cookies=token_info)
        logger.success("Получен ответ от промежуточной аттестации")
        text = attestation_request.text
        attestation_info = json.loads(text)
        logger.debug(f"ATTESTATION INFO: {attestation_info}")
        return attestation_info

    @staticmethod
    async def async_get_exams(token_info: dict, client: httpx.AsyncClient) -> list[dict]:
        """
        Получение промежуточной аттестации студента в асинхронном режиме.
        :param client: Клиент httpx
        :param token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие.
        :return: Лист из словарей с информацией об экзаменах
        """
        logger.info("Отправление запроса на получение экзаменов")
        exams_request = await client.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getProgress",
            "args": "production"
        }, cookies=token_info)
        logger.success("Получен ответ от экзаменов")
        text = exams_request.text
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
