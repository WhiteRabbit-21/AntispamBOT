import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from dotenv import load_dotenv

# --- Настройки ---
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))
TOKEN = os.getenv("TOKEN")  # переменная окружения на Railway
print("TOKEN:", TOKEN)
if not TOKEN:
    raise ValueError("❌ TOKEN не найден! Проверь переменные окружения.")
bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# --- Список "спам-слов" ---
SPAM_WORDS = [
    "крипто", "нфт", "казино", "ставки", "заработок",
    "crypto", "nft", "casino", "bet", "earn money"
]

# --- Команда /start ---
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer(
        "👋 Привет! Я бот, который удаляет сообщения по заданным словам. "
        "Добавь меня в группу и дай права администратора."
    )
    logging.info("Бот получил команду /start от %s", message.from_user.id)

# --- Обработка всех сообщений ---
@router.message()
async def handle_message(message: types.Message):
    if message.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
        return
    if message.from_user.is_bot:
        return
    text = (message.text or message.caption or "").lower()
    username = message.from_user.username or f"id:{message.from_user.id}"

    if any(word in text for word in SPAM_WORDS):
        try:
            chat_member = await bot.get_chat_member(message.chat.id, (await bot.get_me()).id)
            if chat_member.can_delete_messages:
                await message.delete()
                logging.info("🗑 Сообщение от @%s удалено (содержало спам-слово)", username)
            else:
                logging.warning("⚠️ Бот не имеет прав на удаление сообщений в чате")
        except Exception as e:
            logging.error("Ошибка при удалении сообщения: %s", e)

# --- Запуск бота ---
async def main():
    logging.info("🤖 AntiSpam Bot запущен и слушает сообщения...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    if hasattr(asyncio, "WindowsSelectorEventLoopPolicy"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
