import asyncio
import calendar
import os
import json
import logging
from aiogram.dispatcher.filters import Text
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
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


class Book(StatesGroup):
    type = State()
    amount = State()
    date = State()
    time = State()
    duration = State()
    add = State()
    name = State()
    phone = State()
    finish = State()


first_state_keyboard_buttons = [
    [
        types.KeyboardButton(text='Vr'),
        types.KeyboardButton(text='Планета 1'),
        types.KeyboardButton(text='Планета 2'),
    ],
]

vr_amount_keyboard_buttons = [
    [
        types.KeyboardButton(text='1'),
        types.KeyboardButton(text='2'),
        types.KeyboardButton(text='3'),
        types.KeyboardButton(text='Все свободные'),
    ],
]

firs_planet_amount_keyboard_buttons = [
    [
        types.KeyboardButton(text='1'),
        types.KeyboardButton(text='2'),
        types.KeyboardButton(text='3'),
        types.KeyboardButton(text='Все свободные'),
    ],
]

second_planet_amount_keyboard_buttons = [
    [
        types.KeyboardButton(text='1'),
        types.KeyboardButton(text='2'),
        types.KeyboardButton(text='3'),
        types.KeyboardButton(text='Все свободные'),
    ],
]

date_keyboard_buttons = [
    [
        types.KeyboardButton(text="Этот этап возможно сделать с использованием календаря"),
    ]
]

time_keyboard_buttons = [
    [
        types.KeyboardButton(text='12:00'),
        types.KeyboardButton(text='13:00'),
        types.KeyboardButton(text='14:00'),
    ]
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


book_data = {
    'type': None,
    'amount': None,
    'date': None,
    'time': None,
    'duration': None,
}

user_data = {
    'name': None,
    'phone': None,
}

list_of_current_bookings = []


# Start the bot and choose the type of book
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):

    await Book.type.set()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=first_state_keyboard_buttons)

    await message.reply("Привет! Вот доступные категории бронирования", reply_markup=markup)


# handle cancelling
@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        return
    logging.info(f'Cancelling state: {current_state}')
    await state.finish()
    await message.reply('Cancelled.', reply_markup=types.ReplyKeyboardRemove())


# save the chosen "type" answer from user and set the next state
@dp.message_handler(state=Book.type)
async def process_type(message: types.Message, state: FSMContext):

    async with state.proxy() as data:
        data['type'] = message.text
    #print(f"type: {data['type']}")
    book_data['type'] = data['type']

    # save data['type'] as answer
    await Book.next()
    if data['type'] == 'Vr':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=vr_amount_keyboard_buttons)
    elif data['type'] == 'Планета 1':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=firs_planet_amount_keyboard_buttons)
    elif data['type'] == 'Планета 2':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=second_planet_amount_keyboard_buttons)
    else:
        markup = None
    await message.reply('Выберите количество персон', reply_markup=markup)


# save the chosen "amount" answer from user and set the next state
@dp.message_handler(state=Book.amount)
async def process_amount(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['amount'] = message.text
    #print(f"amount: {data['amount']}")
    book_data['amount'] = data['amount']
    # save data['amount'] as answer
    await Book.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=date_keyboard_buttons)
    await message.answer("Выберите дату", reply_markup=markup)


# save the date and set next state
@dp.message_handler(state=Book.date)
async def process_date(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['date'] = message.text
    # save data['date'] as answer
    book_data['date'] = data['date']
    #print(f"date: {data['date']}")
    await Book.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=time_keyboard_buttons)
    await message.answer("Выберите время", reply_markup=markup)


# save the time and set next state
@dp.message_handler(state=Book.time)
async def process_time(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['time'] = message.text
    # save data['time'] as answer
    book_data['time'] = data['time']
    #print(f"time: {data['time']}")
    await Book.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=duration_keyboard_buttons)
    await message.answer("Выберите продолжительность посещения", reply_markup=markup)


# save duration and set next state
@dp.message_handler(state=Book.duration)
async def process_duration(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['duration'] = message.text
    #print(f"duration: {data['duration']}")
    book_data['duration'] = data['duration']
    # save data['duration'] as answer
    await Book.next()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=add_keyboard_buttons)
    await message.answer(text='Чето там туда сюда может текст и не нужен :)', reply_markup=markup)


# process add state
@dp.message_handler(state=Book.add)
async def process_state(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['add'] = message.text

    if data['add'] == 'Это все чего я хочу':
        booking = (book_data['type'], book_data['amount'], book_data['date'], book_data['time'], book_data['duration'], message.chat.id)
        list_of_current_bookings.append(booking)
        print(f"CREATE: Book:{book_data} was created")
        await Book.next()
        await message.answer("Введите ваше имя")
    else:
        booking = (book_data['type'], book_data['amount'], book_data['date'], book_data['time'], book_data['duration'],
                   message.chat.id)
        list_of_current_bookings.append(booking)
        print(f"CREATE: Book:{book_data} was created")

        await Book.type.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, selective=True, one_time_keyboard=True, keyboard=first_state_keyboard_buttons)
        await message.reply("Вот доступные категории бронирования", reply_markup=markup)


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
    user = (message.chat.id, message.chat.username, user_data['name'], user_data['phone'])

    # print(data_base.exist_in_users(conn, message.chat.id))
    if not await async_data_base.exist_in_users(conn, message.chat.id):
        await async_data_base.create_user(conn, user)
        print(f"CREATE: User_id: {message.chat.id} | Book: {book_data}")

    else:
        await async_data_base.update_user(conn, (user_data['name'], user_data['phone'], message.chat.id))
        await conn.commit()
        print(f"UPDATE: User_id: {message.chat.id} | Book: {book_data}")

    for booking in list_of_current_bookings:
        await async_data_base.create_booking(conn, booking)
    await conn.commit()
    await conn.close()
    await state.finish()


async def shutdown(dispatcher: Dispatcher):
    await dispatcher.storage.close()
    await dispatcher.storage.wait_closed()

if __name__ == '__main__':
    executor.start_polling(dp, on_shutdown=shutdown)
