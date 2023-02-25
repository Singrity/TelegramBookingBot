import asyncio
import calendar
import os
from datetime import date
import json
import logging
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils.deep_linking import get_start_link, decode_payload
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Calendar
from aiogram_calendar import simple_cal_callback, SimpleCalendar, dialog_cal_callback, DialogCalendar



from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
#import google_calendar
import async_data_base

storage = MemoryStorage()

TOKEN_FILE = open("variables/bot_token.json")

API_TOKEN = json.load(TOKEN_FILE)['ERABOT_TOKEN']

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())


MAX_CAPACITY = {
    'bel': 10,
    'mol': 80,
    'sel': 30,
}


class Book(StatesGroup):
    club = State()
    type = State()
    date = State()
    time = State()
    amount = State()
    duration = State()
    name = State()
    phone = State()
    finish = State()


club_keyboard_buttons = [
    [
        types.KeyboardButton(text='Беляево'),
        types.KeyboardButton(text='Селигерская'),
        types.KeyboardButton(text='Молодёжная'),
    ],
]


duration_keyboard_buttons = [
    [
        types.KeyboardButton(text='1 час'),
        types.KeyboardButton(text='2 часа'),
        types.KeyboardButton(text='3 часа'),
        types.KeyboardButton(text='Целый день'),
        types.KeyboardButton(text='Задать время в ручную?'),
    ]
]

add_keyboard_buttons = [
    [
        types.KeyboardButton(text="Добавить тип бронирования"),
        types.KeyboardButton(text="Это все чего я хочу"),
    ]
]

# bel_link = await get_start_link('bel', encode=True)
# sel_link = await get_start_link('sel', encode=True)
# mol_link = await get_start_link('mol', encode=True)


link_params = {
    'club': '',
}

book_data = {
    'type': None,
    'amount': None,
    'date': None,
    'time': None,
    'duration': None,
    'club': None,
}

user_data = {
    'name': None,
    'phone': None,
    'id': None,
}

param_from_link_to_club = {
    'bel': 'Беляево',
    'sel': 'Селигерская',
    'mol': 'Молодёжная'
}

club_to_file = {
    'Беляево': 'Belyaevo.json',
    'Селигерская': 'Seligerskaya.json',
    'Молодёжная': 'Molodejnaya.json',
}
list_of_current_bookings = []




@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info(f'Cancelling state: {current_state}')
    await state.finish()
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=['calendar'])
async def cmd_calendar(message: types.Message):
    await Book.date.set()
    await message.answer("Select date", reply_markup=await SimpleCalendar().start_calendar())


@dp.message_handler(commands=['get_dates'])
async def get_dates(message: types.Message):
    conn = await async_data_base.create_connection('era_data_base.db')
    await async_data_base.get_free_time(conn)


# Start the bot and choose the type of book
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    user_data['id'] = message.chat.id
    args = message.get_args()
    param = decode_payload(args)
    link_params['club'] = param
    logging.info(f"User: {user_data['id']} started with parameter: {param}")
    await Book.club.set()
    if param:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True,
                                           keyboard=[
                                               [
                                                   types.KeyboardButton(text=f'Записаться в текущий клуб: {param_from_link_to_club[param]}'),
                                                   types.KeyboardButton(text="Селигерская"),
                                                   types.KeyboardButton(text="Беляево"),
                                                   types.KeyboardButton(text="Молодёжная"),
                                               ],
                                           ])
        await message.reply(f"Привет! Выбери клуб в который ты хочешь записаться", reply_markup=markup)
    else:

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True,
                                           keyboard=club_keyboard_buttons)
        await message.reply("Привет!\nВыбери клуб в который ты хочешь записаться ", reply_markup=markup)


@dp.message_handler(state=Book.club)
async def process_club(message: types.Message, state: FSMContext):
    text_message = message.text.split(': ')
    if text_message[0] == 'Записаться в текущий клуб':
        async with state.proxy() as data:
            data['club'] = param_from_link_to_club[link_params['club']]
            book_data['club'] = data['club']
    else:
        async with state.proxy() as data:
            data['club'] = message.text
            book_data['club'] = data['club']
    with open(f'clubs_data/{club_to_file[book_data["club"]]}', 'r', encoding='utf-8') as file:
        file_data = json.load(file)
    club_types = file_data['types']
    keyboard = [[types.KeyboardButton(text=f"{booking_type}")] for booking_type in club_types]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True,
                                           keyboard=keyboard)
    await message.answer("Выберите тип бронирования", reply_markup=markup)
    await Book.next()


@dp.message_handler(state=Book.type)
async def process_type(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['type'] = message.text
    book_data['type'] = data['type']

    await message.reply('Выберите дату', reply_markup=await SimpleCalendar().start_calendar())
    await Book.next()


@dp.callback_query_handler(simple_cal_callback.filter(), state=Book.date)
async def process_calendar(callback_query: types.CallbackQuery, callback_data: dict):
    selected, date = await SimpleCalendar().process_selection(callback_query, callback_data)
    if selected:
        await callback_query.message.answer(date.strftime("%d.%m.%y"))
        book_data['date'] = date.strftime("%d/%m/%y")
    await Book.next()

    await callback_query.message.answer("Выберите время", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Book.time)
async def process_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = message.text
    # save data['time'] as answer
    book_data['time'] = data['time']
    #print(f"time: {data['time']}")
    await Book.next()
   # markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=types.ReplyKeyboardRemove())
    await message.answer("Укажите колчество человек", reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(state=Book.amount)
async def process_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = message.text

    book_data['amount'] = data['amount']
    # save data['amount'] as answer
    await Book.next()
    await message.answer("Укажите продолжительность", reply_markup=types.ReplyKeyboardRemove())



# save duration and set next state
@dp.message_handler(state=Book.duration)
async def process_duration(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['duration'] = message.text
    #print(f"duration: {data['duration']}")
    book_data['duration'] = data['duration']
    # save data['duration'] as answer
    # TODO: If user exists in database, offer to update the name and phone number or leave them the same.
    #  This also allows custom greetings on start
    await Book.next()

    await message.answer(text='Введите ваше имя', reply_markup=types.ReplyKeyboardRemove())


# process add state

@dp.message_handler(state=Book.name)
async def process_name(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['name'] = message.text
    user_data['name'] = data['name']

    await Book.phone.set()
    await message.answer("Укажите ваш номер телефона")


@dp.message_handler(state=Book.phone)
async def process_phone(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.text
    user_data['phone'] = data['phone']

    await Book.next()
    await message.answer("Спасибо за бронирование!")
    await finish(message, state)


async def finish(message: types.Message, state: FSMContext):
    conn = await async_data_base.create_connection('era_data_base.db')
    await async_data_base.create_tables(conn)
    async with state.proxy() as data:
        user = (user_data['id'], message.chat.username, user_data['name'], user_data['phone'], data['club'])

    # print(data_base.exist_in_users(conn, message.chat.id))
    if not await async_data_base.exist_in_users(conn, user_data['id']):
        await async_data_base.create_user(conn, user)
        print(f"CREATE: User_id: {user_data['id']} | Book: {book_data}")

    else:
        await async_data_base.update_user(conn, (user_data['name'], user_data['phone'],  user_data['id']))
        await conn.commit()
        print(f"UPDATE: User_id: {user_data['id']} | Book: {book_data}")

    booking = (book_data['type'], book_data['amount'], book_data['date'], book_data['time'], book_data['duration'],
               user_data['id'], book_data['club'])
    await async_data_base.create_booking(conn, booking)
    await conn.commit()
    await conn.close()
    await state.finish()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)

