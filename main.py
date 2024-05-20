import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

API_TOKEN = '7125040391:AAEHB2ZALmJbDLowzY7wHkbzF6S_MfWTMiI'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class MyStates(StatesGroup):
    poll_question = State()
    poll_options = State()


user_polls = {}


@dp.message_handler(commands=['create_poll'])
async def create_poll(message: types.Message):
    await message.answer("Enter your poll question:")
    await MyStates.poll_question.set()


@dp.message_handler(state=MyStates.poll_question)
async def process_poll_question(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['question'] = message.text
    await message.answer("Enter the poll options separated by commas:")

    await MyStates.poll_options.set()


@dp.message_handler(state=MyStates.poll_options)
async def process_poll_options(message: types.Message, state: FSMContext):
    # Save the poll options
    async with state.proxy() as data:
        data['options'] = message.text.split(',')

    user_id = message.from_user.id
    if user_id not in user_polls:
        user_polls[user_id] = []
    user_polls[user_id].append({
        'question': data['question'],
        'options': data['options'],
    })
    await state.finish()
    await message.answer("Poll created successfully!")


@dp.message_handler(commands=['my_polls'])
async def my_polls(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_polls:
        polls = user_polls[user_id]
        response = "Your polls:\n"
        for index, poll in enumerate(polls, start=1):
            response += f"{index}. {poll['question']}\nOptions: {', '.join(poll['options'])}\n"
        await message.answer(response)
    else:
        await message.answer("You haven't created any polls yet.")


@dp.message_handler(commands=['participate'])
async def participate(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_polls:
        polls = user_polls[user_id]
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        for index, poll in enumerate(polls, start=1):
            keyboard.add(types.InlineKeyboardButton(text=poll['question'], callback_data=f"participate_{index}"))
        await message.answer("Choose a poll to participate:", reply_markup=keyboard)
    else:
        await message.answer("You haven't created any polls yet.")


@dp.callback_query_handler(lambda c: c.data.startswith('participate_'))
async def participate_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    index = int(callback_query.data.split('_')[1]) - 1
    if user_id in user_polls:
        polls = user_polls[user_id]
        if 0 <= index < len(polls):
            poll = polls[index]
            if 'participants' not in poll:
                poll['participants'] = set()
            poll['participants'].add(user_id)
            await callback_query.answer(f"You chose to participate in the poll: {poll['question']}")
        else:
            await callback_query.answer("Invalid poll selection.")
    else:
        await callback_query.answer("You haven't created any polls yet.")


@dp.message_handler()
async def echo(message: types.Message):
    await message.answer("I don't understand that command. Please use /create_poll, /my_polls, or /participate.")


executor.start_polling(dp)
