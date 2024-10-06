import asyncio 
import sqlite3
import random
import string
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardButton, FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

API_TOKEN = '7363228019:AAHEAqWQ1X-34qt3QN45Q5KRio2dOz_QTQo'
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
conn = sqlite3.connect('crypto_cat.db')
cursor = conn.cursor()
FRONTEND_URL = 'http://127.0.0.1:5500'

def init_db():
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY,
                       username TEXT NOT NULL,
                       coins INTEGER DEFAULT 0,
                       referral_code TEXT UNIQUE)''')
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'referral_code' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT")
    conn.commit()

def generate_referral_code():
    while True:
        code = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        cursor.execute('SELECT COUNT(*) FROM users WHERE referral_code = ?', (code,))
        if cursor.fetchone()[0] == 0:
            return code

def get_or_create_user(user_id: int, username: str):
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    if user is None:
        referral_code = generate_referral_code()
        cursor.execute('''INSERT INTO users (user_id, username, coins, referral_code) 
                          VALUES (?, ?, 0, ?)''', (user_id, username, referral_code))
        conn.commit()
        return cursor.lastrowid
    return user[0]

@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    try:
        user = message.from_user
        username = user.username if user.username else user.first_name 
        user_id = get_or_create_user(user.id, username)
        
        cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user.id,))
        referral_code = cursor.fetchone()[0]
        
        game_link = f"{FRONTEND_URL}/?username={username}&referral={referral_code}"
        photo = FSInputFile("cat_photo.webp")
        inline_kb = InlineKeyboardBuilder()
        inline_kb.row(InlineKeyboardButton(text='What to do?🙀', callback_data='info'))
        inline_kb.row(InlineKeyboardButton(text='Play🧶', url=game_link))

        await message.answer_photo(
            photo,
            caption=(f"Welcome to the crypto world, {username}! I'm @Tap_cat, your friendly crypto bot.\n"
                     "Don't be afraid to choose your strategy: farm Cat points, complete tasks, invite friends, and buy boosters!\n\n"
                     f"Your referral code is: {referral_code}\n"
                     "Share it with friends to earn bonus coins!\n\n"
                     "Meow, and may your crypto journey be exciting and profitable!!!!\n\n"
                     "We are always in touch \n\n"
                     "Crypto_Cat 😼"),
            reply_markup=inline_kb.as_markup()
        )
    except Exception as e:
        print(f"Error in send_welcome: {e}")

@dp.callback_query(lambda c: c.data == 'info')
async def process_callback_info(callback_query: types.CallbackQuery):
    user = callback_query.from_user
    username = user.username or user.first_name
    game_link = f"{FRONTEND_URL}/?username={username}"
    kb = InlineKeyboardBuilder()
    kb.row(InlineKeyboardButton(text='Play🧶', url=game_link))

    await callback_query.answer()
    await bot.send_message(
        chat_id=callback_query.from_user.id,
        text=("🐾 Tap Coins: Earn crypto coins for actions like viewing content or participating in events.\n\n"
              "🐾 Use Coins: Get rewards, discounts, or privileges on the platform.\n\n"
              "🐾 Balance Updates: Your balance updates automatically.\n\n"
              "🐾 Privacy: We don't store personal info. All transactions are secure."),
        reply_markup=kb.as_markup()
    )

async def main():
    init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        conn.close()
