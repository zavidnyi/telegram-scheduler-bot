import logging
import asyncio
from aiogram import Bot, types
from config import BOT_TOKEN
import sys

bot = Bot(token=BOT_TOKEN)
logging.basicConfig(level=logging.INFO)

chat_to_send, text_to_send = int(sys.argv[1]), sys.argv[2]


async def main(chat_id: int, text: str):
    await bot.send_message(chat_id=chat_id, text=text, parse_mode=types.ParseMode.HTML)
    await bot.close()


if __name__ == "__main__":
    try:
        print(chat_to_send, text_to_send)
        # honestly no idea why this doesnt work me and 10 other people have
        # tried different options and only this one just works
        # well, if it works its good enough I guess......
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(chat_id=chat_to_send, text=text_to_send))
        loop.close()
    except Exception as exception:
        with open("error_journal.txt", "w") as journal:
            journal += "Exception was raised: {0!s}".format(str(exception))
            journal.close()
