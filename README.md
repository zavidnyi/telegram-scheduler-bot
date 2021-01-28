# telegram-scheduler-bot

To implement:
- time_zone support
- troll protection
- VIP users
- Customizable event frequency

# How it works:
  The bot utilizes the aiogram library to interact with Telegram API using python. The user files are stored in JSON file (ujson encoder and decoder is used as it is faster). Once the user has set up an event he will receive notifications for it every week 30 minutes before the event. The notifications are setted up as cron jobs (python-crontab) is used to manage cron jobs.
