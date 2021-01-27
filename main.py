#!venv/bin/python
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher.filters import Text
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from os import listdir
from time import strptime, sleep
from utility import generate_event_text
from notifications_manager import set_up_notification, delete_notification
from config import BOT_TOKEN
import ujson


# We set up bot and storage in RAM in order to save user states
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)


# The states of user interaction we need
class SetEvent(StatesGroup):
    waiting_for_eventnum = State()
    waiting_for_event_name = State()
    waiting_for_event_time = State()
    waiting_for_event_weekday = State()
    waiting_for_event_location = State()
    waiting_for_event_extra = State()
    finishing_up = State()


async def display_main_menu(message: types.Message):
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    buttons = [
        types.InlineKeyboardButton(text="Display my events", callback_data="display"),
        types.InlineKeyboardButton(text="Add an event", callback_data="add_custom")
    ]
    keyboard.add(*buttons)
    await message.edit_text(text="Please choose an option:", reply_markup=keyboard)


# Handler for command /start (start of conversation with user)
@dp.message_handler(commands="start")
async def cmd_start(message: types.Message):
    # Check if we already have a file for this user
    for file in listdir("users"):
        if file.startswith(str(message.from_user.id)):
            await message.answer("You already have an account")
            break
    else: # if doesnt brake above
        # We create a file for user where we will store all information we need
        with open("users/" + str(message.from_user.id) + ".json", "w") as user_file:
            data = {
                "user_id": str(message.from_user.id),
                "records": 0,
                "events": []
            }
            ujson.dump(data, user_file)
            user_file.close()

        # We create inline keyboard and buttons which will trigger our callbacks
        # handlers
        keyboard = types.InlineKeyboardMarkup()
        button_standart = types.InlineKeyboardButton(text="Create recommended schedule", callback_data="add_recommended")
        button_custom = types.InlineKeyboardButton(text="Create custom Schedule", callback_data="add_custom")
        keyboard.add(button_standart)
        keyboard.add(button_custom)

        await message.answer(text="Please choose an option....", reply_markup=keyboard)


@dp.callback_query_handler(text="add_recommended")
async def add_recommended(call: types.CallbackQuery):
    await call.message.answer(text="Recommended events have been added to your schedule!")
    await display_main_menu(call.message)
    await call.answer()


@dp.callback_query_handler(text="add_custom")
async def add_custom(call: types.CallbackQuery):
    # We open a user file and check that he hasnt exceeded the limit for records
    user_file = open("users/" + str(call.from_user.id) + ".json", "r")
    user_data = ujson.load(user_file)
    # we restrict amount of records user can have so that he doesn't abuse the bot
    # might be a good idea to implement VIP users????
    if user_data["records"] >= 8:
        await call.message.answer(text="You can't create more records!")
        sleep(1)
        await display_main_menu(call.message)
    else:
        await SetEvent.waiting_for_event_name.set()
        await call.message.answer(text="Please input the name of the event:")

    # This coroutine is necessarily to let Telegram servers know that we have processed
    # the callback query
    await call.answer()


@dp.message_handler(state=SetEvent.waiting_for_event_name, content_types=types.ContentTypes.TEXT)
async def get_event_name(message: types.Message, state: FSMContext):
    # We store all users input into memory to later write it to user file
    # (the data from "state" is stored as a dictionary)
    await state.update_data(event_name=message.text)
    await message.answer(text="Please input the time when event occurs in following format:\nHH:MM (24-hour standart)")
    await SetEvent.next()


@dp.message_handler(state=SetEvent.waiting_for_event_time)
async def get_event_time(message: types.Message, state: FSMContext):
    # We use "time" module to process users input
    # if user gave us incorrect input we ask him to try again
    # ("ValueError" is raised by time.strptime() function when it cant process the arguments)
    try:
        strptime(message.text, "%H:%M")
    except ValueError:
        await message.answer(text="Your input was incorrect, please try again")
        await SetEvent.waiting_for_event_time.set()
        return
    await state.update_data(event_time=message.text)
    await message.answer(text="Please input the full name of the day of the week the event is going to occur:")
    await SetEvent.next()


@dp.message_handler(state=SetEvent.waiting_for_event_weekday)
async def get_event_weekday(message: types.Message, state: FSMContext):
    # Here we do the same process as for time
    try:
        strptime(message.text, "%A")
    except ValueError:
        await message.answer(text="Your input was incorrect, please try again")
        await SetEvent.waiting_for_event_weekday.set()
        return
    await state.update_data(event_wday=message.text)
    await message.answer(text="Please input the location of the event")
    await SetEvent.next()


@dp.message_handler(state=SetEvent.waiting_for_event_location)
async def get_event_time(message: types.Message, state: FSMContext):
    await state.update_data(event_location=message.text)
    await message.answer(text="Additional information:")
    await SetEvent.next()


@dp.message_handler(state=SetEvent.waiting_for_event_extra)
async def get_event_time(message: types.Message, state: FSMContext):
    # We ask user for the final piece of data
    # Then via inline keyboard callback handler is called which
    # will either confirm the creation of the even and write it to the user file
    # or will erase all the information we have gathered from user
    await state.update_data(event_extra=message.text)
    buttons = [
        types.InlineKeyboardButton(text="Confirm", callback_data="create_event"),
        types.InlineKeyboardButton(text="Cancel", callback_data="forget"),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await message.answer(text="Please confirm event creation:", reply_markup=keyboard)
    await SetEvent.next()


@dp.callback_query_handler(text="create_event", state=SetEvent.finishing_up)
async def create_event(call: types.CallbackQuery, state: FSMContext):
    event = await state.get_data()
    await state.finish()
    await state.reset_state()
    user_file = open("users/" + str(call.from_user.id) + ".json", "r")
    user_data = ujson.load(user_file)
    user_data["records"] += 1
    user_data["events"].append({})
    user_data["events"][user_data["records"] - 1] = event
    user_data["events"][user_data["records"] - 1]["event_id"] = hash(call.from_user.id + int(event["event_time"][0:2]))
    set_up_notification(chat_id=call.message.chat.id,
                        event=user_data["events"][user_data["records"] - 1]
                        )
    user_data["events"][user_data["records"] - 1]["reminder_set"] = False
    user_file = open("users/" + str(call.from_user.id) + ".json", "w")
    ujson.dump(user_data, user_file)
    await call.answer()
    await display_main_menu(call.message)


@dp.callback_query_handler(text="forget", state=SetEvent.finishing_up)
async def forget_event(call: types.CallbackQuery, state: FSMContext):
    print(call.message.chat.id)
    await state.finish()
    await state.reset_state()
    await call.answer()
    await display_main_menu(call.message)


# We Display users events as buttons on which he can click to see an event details!
@dp.callback_query_handler(text="display")
async def display_events(call: types.CallbackQuery):
    user_file = open("users/" + str(call.from_user.id) + ".json", "r")
    user_data = ujson.load(user_file)
    buttons = []
    n_records = user_data["records"]
    for i in range(n_records):
        event = user_data["events"][i]
        buttons.append(types.InlineKeyboardButton(text=event["event_name"], callback_data=("disp_" + str(i))))
    button = types.InlineKeyboardButton(text="<< Back", callback_data="main_menu")
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(*buttons)
    keyboard.row(button)
    await call.answer()
    await call.message.edit_text(text="Please choose an even to view", reply_markup=keyboard)


# Shows user a details of the event he cliked on
@dp.callback_query_handler(Text(startswith="disp_"))
async def show_event(call: types.CallbackQuery):
    event_num = int(call.data.split("_")[1])
    user_file = open("users/" + str(call.from_user.id) + ".json", "r")
    user_data = ujson.load(user_file)
    event = user_data["events"][event_num]
    # we user html <b> tag to make text bold
    event_output = generate_event_text(event)
    buttons = [
        types.InlineKeyboardButton(text="<< Back", callback_data="main_menu"),
        types.InlineKeyboardButton(text="Delete", callback_data=("del_" + str(event_num)))
    ]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(*buttons)
    await call.answer()
    await call.message.edit_text(text=event_output, parse_mode=types.ParseMode.HTML, reply_markup=keyboard)


@dp.callback_query_handler(text="main_menu")
async def show_main_menu(call: types.CallbackQuery):
    await call.answer()
    await display_main_menu(call.message)


@dp.callback_query_handler(Text(startswith="del_"))
async def delete_event(call: types.CallbackQuery):
    event_num = int(call.data.split("_")[1])
    user_file = open("users/" + str(call.from_user.id) + ".json", "r")
    user_data = ujson.load(user_file)
    delete_notification(event_id=user_data["events"][event_num]["event_id"])
    user_data["events"].pop(event_num)
    user_data["records"] -= 1
    user_file = open("users/" + str(call.from_user.id) + ".json", "w")
    ujson.dump(user_data, user_file)
    await call.answer()
    await display_main_menu(call.message)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
