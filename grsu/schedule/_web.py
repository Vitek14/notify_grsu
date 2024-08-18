import grequests
import json
from datetime import datetime, timedelta
from ..exceptions import ScheduleNotFound


def get_raw_schedule(self, groups_id: list) -> list:
    current_date = datetime.today()
    two_weeks_ago = current_date - timedelta(weeks=2)
    two_month_after = current_date + timedelta(weeks=9)

    month_after_formatted = two_month_after.strftime("%d.%m.%Y")
    week_ago_formatted = two_weeks_ago.strftime("%d.%m.%Y")

    requests = []
    for group_id in groups_id:
        # Если нет определённой лабораторной группы у студента(None)
        if not group_id:
            continue
        group_schedule = grequests.get(f"https://api.grsu.by/1.x/app1/getGroupSchedule?groupId={group_id}&dateStart="
                                       f"{week_ago_formatted}&dateEnd={month_after_formatted}&lang=ru_RU")

        requests.append(group_schedule)

    responses = grequests.map(requests, stream=True)
    responses_with_groups = list(zip(groups_id, responses))
    return responses_with_groups


def process_schedule(self, raw_schedule: list) -> list | None:
    group_schedule_list = []
    for group_schedule in raw_schedule:
        group_id = group_schedule[0]
        json_group_schedule = json.loads(group_schedule[1].text)

        # Если в расписании нет по факту расписания
        if json_group_schedule["count"] == 0:
            continue
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
                group_schedule_list.append((name, lesson_type, place, room, teacher, date, day_num, start_time, end_time, group_id, subgroup_id))
    return group_schedule_list
