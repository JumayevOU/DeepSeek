import logging
import asyncio
import aiohttp
import pytesseract
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.types import ParseMode
from PIL import Image
from io import BytesIO

API_TOKEN = '7574290945:AAFWuPAX0IGt9CN5Gz6evxJbW-B_crRuyjg'

url = "https://deepseek-all-in-one.p.rapidapi.com/reasoner"
headers = {
    "x-rapidapi-key": "8225c08d34msh8a0e7f40dd28af2p10f31cjsn901221c12d69",
    "x-rapidapi-host": "deepseek-all-in-one.p.rapidapi.com",
    "Content-Type": "application/json"
}

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

async def get_response_from_deepseek(user_message: str):
    payload = {
        "messages": [{"role": "user", "content": user_message}]
    }

    for _ in range(5):  
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 429:
                        logging.warning("429: Too many requests. Waiting...")
                        await asyncio.sleep(10)
                        continue
                    response.raise_for_status()
                    return await response.json()
        except Exception as e:
            logging.error(f"Xatolik: {e}")
            return None
    return None

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    info_text = (
        "👋 <b>Keling tanishib olaylik!</b>\n\n"
        "🤖 Men sizning AI yordamchingizman. Quyidagilarni qila olaman:\n"
        "➤ Matnli savollaringizga javob beraman\n"
        "➤ Rasm yuborsangiz, ichidagi matnni o‘qib tushunaman\n"
        "➤ Har qanday mavzuda izoh, yechim yoki maslahat bera olaman\n\n"
        "✍️ Savolingizni yozing yoki rasm yuboring. Boshladikmi?"
    )
    await message.answer(info_text, parse_mode=ParseMode.HTML)

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def handle_photo(message: types.Message):
    photo = message.photo[-1]
    photo_file = await photo.download(destination=BytesIO())
    photo_file.seek(0)

    try:
        img = Image.open(photo_file)
        text = pytesseract.image_to_string(img)
        if not text.strip():
            await message.reply("Rasmda matn topilmadi.")
            return
        await message.reply("📝 Rasmda aniqlangan matn:\n" + text)

      
        response_data = await get_response_from_deepseek(text)
        if response_data and "choices" in response_data:
            answer = response_data["choices"][0]["message"]["content"]
            await message.reply("🤖 Javob:\n" + answer)
        else:
            await message.reply("AI javob bera olmadi. Keyinroq urinib ko‘ring.")
    except Exception as e:
        logging.error(e)
        await message.reply("❌ Rasmni o‘qishda xatolik yuz berdi.")

@dp.message_handler(content_types=types.ContentType.TEXT)
async def handle_text(message: types.Message):
    user_message = message.text
    response_data = await get_response_from_deepseek(user_message)

    if response_data and "choices" in response_data:
        answer = response_data["choices"][0]["message"]["content"]
        await message.reply(answer)
    else:
        await message.reply("🤖 Afsuski, javob bera olmadim. Keyinroq urinib ko‘ring.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
