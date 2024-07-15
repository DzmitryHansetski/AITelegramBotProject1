import os
import httpx
import asyncio

from asyncio import sleep

from openai import AsyncOpenAI

from aiogram import Bot, Dispatcher, F
from aiogram import Router
from aiogram.types import Message, KeyboardButton, ReplyKeyboardMarkup
from aiogram.filters.command import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types.dice import DiceEmoji
from aiogram.types import InputMediaAnimation

from setting import settings

router: Router = Router()

openai_api_key = settings.TOKEN_API
admin_id = settings.ADMIN_ID
client = AsyncOpenAI(api_key=openai_api_key,
                     http_client=httpx.AsyncClient(proxies=settings.PROXY)
                     )


async def main():
    bot = Bot(token=settings.TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    print('AI-ассистент успешно запущен')
    await dp.start_polling(bot)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await message.answer("Здравствуйте! Вас приветствует AI-ассистент.\n"
                         "Версия GPT-4o.\n"
                         "Напишите Ваш вопрос пожалуйста.\n"
                         "Или давайте сыграем в игру Кости.\n"
                         "\n"
                         "Hello! You are welcomed by the AI-assistant.\n"
                         "The GPT version is 4o.\n"
                         "Please write your question.\n"
                         "Or let's play the Dice game.\n"
                         "\n"
                         "/start - запуск (перезапуск) AI-ассистента (AI-бота).\n"
                         "/start - starting (restarting) the AI-assistant (AI-bot).\n"
                         "\n"
                         "/start_game - начать игру (Start the game)"
                         )
    global kb
    kb = [[KeyboardButton(text="/start 😀"),
           KeyboardButton(text="/start_game 🎲")],
          [KeyboardButton(text="/Написать вопрос 🖌 \n"
                                "Write a question")]
          ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await message.answer("А что выбираете Вы...? 🤔 \n"
                         "And what do you choose...?", reply_markup=keyboard)
    await state.clear()


@router.message(Command("start_game"))
async def cmd_start_game(message: Message):
    dice1 = await message.answer_dice(emoji=DiceEmoji.DICE)
    await sleep(4)
    global value_dice1
    value_dice1 = dice1.dice.value
    await message.answer(f'{value_dice1}')
    await message.answer("Ваш ход!\n"
                         "Your move!")
    kb1 = [[KeyboardButton(text="Играть!\n"
                                "Play!"),
            KeyboardButton(text="Выйти!\n"
                                "Exit!")]
          ]
    keyboard = ReplyKeyboardMarkup(keyboard=kb1+kb, resize_keyboard=True)
    await sleep(1)
    await message.answer("В меню AI-ассистента выберите ИГРАТЬ или ВЫЙТИ!\n"
                         "In the AI-Assistant menu, select PLAY or EXIT!", reply_markup=keyboard)


@router.message(F.text == "Играть!\n"
                          "Play!")
async def cmd_start_game_user(message: Message):
    dice2 = await message.answer_dice(emoji=DiceEmoji.DICE)
    value_dice2 = dice2.dice.value
    await sleep(4)
    await message.answer(f'{value_dice2}')
    if value_dice1 > value_dice2:
        await message.answer("Я выиграл! 😆 \n"
                             "I won!"
                             )
        await sleep(1)
        await message.answer("Для продолжения игры, в меню AI-ассистента \n"
                             "выберите /start_game 🎲 \n"
                             "\n"
                             "To continue the game, go to the AI assistant menu \n"
                             "select /start_game"
                             )
    elif value_dice1 < value_dice2:
        await message.answer("Вы выиграли! 👍 \n"
                             "You've won!"
                             )
        await sleep(1)
        await message.answer("Для продолжения игры, в меню AI-ассистента \n"
                             "выберите /start_game 🎲 \n"
                             "\n"
                             "To continue the game, go to the AI assistant menu \n"
                             "select /start_game"
                             )
    else:
        await message.answer("Ничья! 🤷‍♂️ \n"
                             "It's a draw!")
        await sleep(1)
        await message.answer("Для продолжения игры, в меню AI-ассистента \n"
                             "выберите /start_game 🎲 \n"
                             "\n"
                             "To continue the game, go to the AI assistant menu \n"
                             "select /start_game"
                             )


@router.message(F.text == "Выйти!\n"
                          "Exit!")
async def cmd_exit_game_user(message: Message):
    await sleep(1)
    await message.answer("Вы отказались от игры.\n"
                         "Можете позадавать мне вопросы.\n"
                         "\n"
                         "You gave up the game.\n"
                         "You can ask me questions."
                         )


@router.message(F.text == "/Написать вопрос 🖌 \n"
                          "Write a question")
async def cmd_write_a_question(message: Message):
    await sleep(0.5)
    await message.answer("Отлично! Жду Вашего вопроса, пишите...✍️ \n"
                         "\n"
                         "Great! I am waiting for your question, write...\n"
                         )


async def hourglass_animation(message: Message):
    hourglass = ['⏳', '⌛️']
    message = await message.answer(text=hourglass[0])
    for i in range(1, 10):
        await asyncio.sleep(1)
        await message.answer_text(text=hourglass[i % 2])
        await hourglass_animation(message)


class Generate(StatesGroup):
    text = State()

@router.message(Generate.text)
async def generate_error(message: Message):
    await message.answer("Подождите, Ваше сообщение обрабатывается...⏱\n"
                         "Wait, your message is being processed...")


async def gpt4(question):
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": str(question)}],
        model="gpt-4o"
    )
    return response


@router.message(F.text)
async def generate(message: Message, state: FSMContext):
    await message.answer("Ваш запрос обрабатывается, ожидайте... ⏳\n"
                         "Your request is being processed, please wait...")
    hourglass = ['⏳', '⌛️']
    await message.answer(text=hourglass[0])
    await state.set_state(Generate.text)
    response = await gpt4(message.text)
    await message.answer(response.choices[0].message.content)
    await state.clear()


@router.message()
async def reminder_to_message_type(message: Message):
    await message.answer("Ваше сообщение не является текстовым либо содержит фото или картинку!\n"
                         "Your message is not a text message or contains a photo or picture!")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('AI-ассистент отключен')