import grequests
import json
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
import re

Base = declarative_base()

# Подключаемся к базе данных с данными пользователя
engine = create_engine('sqlite:///user.db')
Base.metadata.create_all(engine)


def get_about(self, token_info: dict) -> dict:
    """
    Получение базовых данных о студенте, включая его имя, курс и т.д
    
    :token_info: Словарь, в котором имеются данные для аутентификации, включая MDL_SSP_AuthToken и другие
    """
    with grequests.Session() as session:
        info_about_student = session.post("https://edu.grsu.by/custom-components/custom-api/ajax-router.php", data={
            "method": "getEmployeesData"
        }, cookies=token_info)
        info = json.loads(info_about_student.text)
    return info


def get_attestation(self, token_info: dict) -> dict:
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
