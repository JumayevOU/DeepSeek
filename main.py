import os
import json
import asyncio
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv  
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.methods import DeleteWebhook
from aiogram.types import Message
import aiohttp

# Load .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
AI_TOKEN = os.getenv("API_TOKEN")

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()



USER_DATA_FILE = "user_activity.json"

def load_user_data():
    try:
        with open(USER_DATA_FILE, "r") as f:
            data = json.load(f)
            return {int(k): datetime.fromisoformat(v) for k, v in data.items()}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump({str(k): v.isoformat() for k, v in data.items()}, f)

def update_user_activity(user_id: int):
    data = load_user_data()
    data[user_id] = datetime.now()
    save_user_data(data)

def get_inactive_users(days=7):
    now = datetime.now()
    data = load_user_data()
    return [user_id for user_id, last_seen in data.items() if now - last_seen > timedelta(days=days)]



@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 <b>Keling tanishib olaylik!</b>\n\n"
        "🤖 Men sizning AI yordamchingizman. Quyidagilarni qila olaman:\n"
        "➤ Matnli savollaringizga javob beraman\n"
        "➤ Har qanday mavzuda izoh, yechim yoki maslahat bera olaman\n\n"
        "✍️ Savolingizni yozing men sizga javob berishga harakat qilaman. Boshladikmi?",
        parse_mode="HTML"
    )

@dp.message()
async def process_message(message: Message):
    update_user_activity(message.from_user.id)  
    loading_msg = await message.answer("🧠 <b>Savolingiz tahlil qilinmoqda...</b>", parse_mode="HTML")

    url = "https://api.intelligence.io.solutions/api/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {AI_TOKEN}",
    }

    data = {
        "model": "deepseek-ai/DeepSeek-R1",
        "messages": [
            {
                "role": "system",
                "content": "Siz foydalanuvchiga foydali javoblar beradigan yordamchisiz.",
            },
            {
                "role": "user",
                "content": message.text
            }
        ],
    }

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json=data) as response:
                response.raise_for_status()
                result = await response.json()

                text = result['choices'][0]['message']['content']
                if '</think>' in text:
                    javob = text.split('</think>\n\n')[1]
                else:
                    javob = text

                await bot.delete_message(chat_id=message.chat.id, message_id=loading_msg.message_id)
                await message.answer(javob, parse_mode="Markdown")
        except Exception as e:
            await bot.delete_message(chat_id=message.chat.id, message_id=loading_msg.message_id)
            await message.answer("❌ Kechirasiz, javob olishda xatolik yuz berdi.")
            print("Xatolik:", e)


async def check_inactive_users():
    while True:
        inactive_users = get_inactive_users(days=7)
        for user_id in inactive_users:
            try:
                await bot.send_message(
                    user_id,
                    "👀 Men seni ko‘rmayapman, nega yordam so‘ramayapsan? Yordam kerak bo‘lsa bemalol yoz 😉"
                )
            except Exception as e:
                print(f"❌ {user_id} ga xabar yuborilmadi:", e)
        await asyncio.sleep(86400)  

async def main():
    await bot(DeleteWebhook(drop_pending_updates=True))
    asyncio.create_task(check_inactive_users())  
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
