import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.methods import DeleteWebhook
from aiogram.types import Message
import aiohttp

TOKEN = '8099616066:AAFMZ8ZzO1D3cEUwjwe5umyt4l3BzpmWlL0'
AI_TOKEN = 'io-v2-eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJvd25lciI6ImM5NzJkNmJiLTg5ZTQtNDg4OS1iNWRhLTE4OWY2MTBhMWNhYiIsImV4cCI6NDkwMDQ1NjkyMn0.LzU-QWm0JsxK8_x81O4scsue78UILkMnFBsfkc5hN9tQBCjkvrbhHEXEdyW9H-N6Mvcp21rW-wSyZBmCB2OukA'

logging.basicConfig(level=logging.INFO)

bot = Bot(TOKEN)
dp = Dispatcher()

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

async def main():
    await bot(DeleteWebhook(drop_pending_updates=True))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
