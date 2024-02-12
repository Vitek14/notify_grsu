import grequests
import json
import datetime

from sqlalchemy.sql.ddl import SchemaDropper

from grsu import schedule

def get_raw_schedule(self, group_id: int) -> dict:
    day = datetime.datetime.today().day
    month = datetime.datetime.today().month
    year = datetime.datetime.today().year
    with grequests.Session() as session:
        group_schedule = session.get(f"https://api.grsu.by/1.x/app1/getGroupSchedule?groupId={group_id}&dateStart={day}.{month}.{year}&dateEnd={day}.{month+1}.{year}&lang=ru_RU")
    json_group_schedule = json.loads(group_schedule.text)
    return json_group_schedule

def process_schedule(self, raw_schedule: dict, group_id: int) -> list:
    schedule = []
    for day in raw_schedule["days"]:
        date = day["date"]
        day_num = int(day["num"])
        for lesson in day["lessons"]:
            name = lesson["title"]
            lesson_type = lesson["type"]
            place = lesson["address"]
            room = lesson["room"]
            teacher = lesson["teacher"]["fullname"]
            start_time = lesson["timeStart"]
            end_time = lesson["timeEnd"]
            subgroup_id = lesson["subgroup"]["id"]
            schedule.append((name, lesson_type, place, room, teacher, date, day_num, start_time, end_time, group_id, subgroup_id))
    return schedule