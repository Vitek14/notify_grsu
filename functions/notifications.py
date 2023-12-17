import asyncio
import sqlite3
from functions.select_info import select_auth_info, get_web_user_info
from functions.parse_marks import get_raw_marks, proccess_marks
from functions.auth import auth

async def timer(bot, seconds):
    print("Таймер запущен")
    await asyncio.sleep(seconds)
    print("Время прошло.")
    # notification_text = ""
    await get_new_marks(bot)
    print("Функция get_new_marks выполнена")
    print("Запуск повторно таймера")
    await timer(bot, 300)

async def get_new_marks(bot):
    db = sqlite3.connect("user.db")
    cursor = db.cursor()

    cursor.execute("SELECT tg_id FROM user_data")
    result = cursor.fetchall()
    for user_id in result[0]:
        result = select_auth_info(user_id)
        info = get_web_user_info(result)

        # Возможно следует поменять
        try:
            info["userInfo"]
        except:
            auth(user_id, result[0][0], result[0][1])
        auth_info = select_auth_info(user_id)
        raw_marks = await get_raw_marks(auth_info)
        new_marks = proccess_marks(user_id, raw_marks, True)
        if len(new_marks) == 0:
            continue
        notification_text = "Новые оценки:\n"
        for mark in new_marks:
            notification_text = f"{notification_text}{mark[0]}: {mark[1]} за {mark[2]}\n" 
            # info = get_web_user_info(result)
        await bot.send_message(chat_id=user_id, text=notification_text)