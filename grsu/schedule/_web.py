import grequests
import json
import datetime

from sqlalchemy.sql.ddl import SchemaDropper

from grsu import schedule

def get_raw_schedule(self, groups_id: list) -> list:
    day = datetime.datetime.today().day
    month = datetime.datetime.today().month
    year = datetime.datetime.today().year

    requests = []
    for group_id in groups_id:
        group_schedule = grequests.get(f"https://api.grsu.by/1.x/app1/getGroupSchedule?groupId={group_id}&dateStart={day}.{month}.{year}&dateEnd={day}.{month+1}.{year}&lang=ru_RU")
        requests.append(group_schedule)
    
    responses = grequests.map(requests, stream=True)
    responses_with_groups = list(zip(groups_id, responses))
    # json_responses = []
        # json_responses.append(json_group_schedule)
    return responses_with_groups

def process_schedule(self, raw_schedule: list) -> list:
    #TEST
    group_schedule = []
    for group_schedule in raw_schedule:
        group_id = group_schedule[0]
        json_group_schedule = json.loads(group_schedule[1].text)
        for day in json_group_schedule["days"]:
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
                subgroup_id = int(lesson["subgroup"]["id"])
                group_schedule.append((name, lesson_type, place, room, teacher, date, day_num, start_time, end_time, group_id, subgroup_id))
    return group_schedule