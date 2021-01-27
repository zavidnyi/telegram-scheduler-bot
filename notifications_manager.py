from aiogram import Dispatcher, Bot
from crontab import *
from config import BOT_TOKEN
from utility import generate_event_text
import logging

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)
logging.basicConfig(level=logging.INFO)

DELAY = -30


def create_job(event_id: int, chat_id: int, text: str, wday: str,  time: str):
    print(event_id, chat_id, text, wday, time)
    my_cron = CronTab(user="zavid")
    command_at = 'python3 /home/zavid/Scheduler_Bot/sender.py {0!s} \'{1!s}\''.format(chat_id, text)
    job = my_cron.new(command=command_at, comment=str(event_id))
    job.enable()
    time = time.split(":")
    job.setall(time[1] + " " + time[0] + " * * " + wday)
    my_cron.write()


def set_up_notification(chat_id: int, event: dict):
    text_to_send = event["event_name"] + " starts in 30 minutes!"
    # text_to_send += generate_event_text(event)
    delayed_time = [int(x) for x in event["event_time"].split(":")]
    delayed_time[1] += DELAY
    while delayed_time[1] < 0:
        delayed_time[0] -= 1
        delayed_time[1] += 60
    if delayed_time[0] < 0:
        delayed_time[0] += 24
    delayed_time = str(delayed_time[0]) + ":" + str(delayed_time[1])
    create_job(event_id=event["event_id"],
               chat_id=chat_id,
               text=text_to_send,
               wday=(event["event_wday"].upper()[0:3]),
               time=delayed_time
               )


def delete_notification(event_id: int):
    cron = CronTab(user="zavid")
    cron.remove_all(comment=str(event_id))
    cron.write()
