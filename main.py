from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from openai import OpenAI
from states import MainGroup
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
from config_reader import config

logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.bot_token.get_secret_value())
dp = Dispatcher()
client = OpenAI()


@dp.message(Command("start"))
async def send_menu(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Choose companion",
            callback_data="choosing_companion")
    )
    await message.answer(
        "Hey!\n\nYou can choose your companion or start chatting right away",
        reply_markup=builder.as_markup()
    )
    await state.update_data(conversation_history=[])
    await state.set_state(MainGroup.main_menu)

@dp.message(Command("menu"))
async def send_menu(message: types.Message, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Choose companion",
            callback_data="choosing_companion")
    )
    await message.answer(
        "Hey!\n\nYou can choose your companion or start chatting right away",
        reply_markup=builder.as_markup()
    )
    await state.update_data(conversation_history=[])
    await state.set_state(MainGroup.main_menu)


@dp.callback_query(F.data == "choosing_companion")
async def choosing_companion_menu(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Back",
            callback_data="main_menu")
    )
    await callback.message.edit_text(
        "Let me know who you want to talk to",
        reply_markup=builder.as_markup()
    )
    await state.set_state(MainGroup.choosing_companion)


@dp.message(MainGroup.choosing_companion)
async def choosing_companion(message: types.Message, state: FSMContext):
    await state.update_data(chosen_companion=message.text)
    await message.answer("Great! you can start chatting")
    await state.update_data(conversation_history=[])
    await state.set_state(MainGroup.common)


@dp.callback_query(F.data == "main_menu")
async def show_menu(callback: types.CallbackQuery, state: FSMContext):
    builder = InlineKeyboardBuilder()
    builder.add(
        types.InlineKeyboardButton(
            text="Choose companion",
            callback_data="choosing_companion")
    )
    await callback.message.edit_text(
        "Hey!\n\nYou can choose your companion or start chatting right away",
        reply_markup=builder.as_markup()
    )
    await state.set_state(MainGroup.main_menu)


@dp.message()
async def send_gpt_answer(message: types.Message, state: FSMContext):
    # Retrieve conversation history or initialize it if not present
    data = await state.get_data()
    chosen_companion = data.get("chosen_companion")
    conversation_history = data.get("conversation_history", [])

    # Add the new user message to the conversation history
    conversation_history.append({"role": "user", "content": message.text})

    # Construct the message list for the API, including system prompt and conversation history
    messages = [
        {"role": "system",
         "content": f"You are {chosen_companion}. You need to impersonate and answer in the way this person would. "
                    f"Never reveal the fact the you are a personal assistant. Whatever user writes, you need to play "
                    f"your role. Be creative"}
    ]
    messages.extend(conversation_history)

    # Make the API call
    completion = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    # Get the response and add it to the conversation history
    response_content = completion.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": response_content})
    print(conversation_history)

    # Update the state with the new history
    await state.update_data(conversation_history=conversation_history)

    # Respond to the user
    await message.answer(response_content)

    max_history_len = 10  # Adjust based on your needs
    if len(conversation_history) > max_history_len:
        await state.update_data(conversation_history=conversation_history[-max_history_len:])


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
