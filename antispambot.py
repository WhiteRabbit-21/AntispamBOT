import os
import logging
from aiogram import Bot, Dispatcher, types, Router
from aiogram.enums import ChatType
from aiogram.filters import CommandStart
from aiohttp import web

# --- Настройки ---
TOKEN = os.getenv("TOKEN")
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
PORT = int(os.getenv("PORT", 8000))

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# --- Список спам-слов ---
SPAM_WORDS = [
    "крипто", "нфт", "казино", "ставки", "заработок",
    "crypto", "nft", "casino", "bet", "earn money"
]

# --- Команда /start ---
@router.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("👋 Привет! Я бот, который удаляет сообщения по заданным словам. Добавь меня в группу и дай права администратора.")
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
                logging.info("🗑 Сообщение от @%s удалено", username)
            else:
                logging.warning("⚠️ Бот не имеет прав на удаление сообщений")
        except Exception as e:
            logging.error("Ошибка при удалении сообщения: %s", e)

# --- Webhook setup ---
async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)
    logging.info(f"Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(app: web.Application):
    logging.info("Удаляем webhook...")
    await bot.delete_webhook()
    await bot.session.close()

async def handle(request: web.Request):
    update = types.Update(**await request.json())
    await dp.process_update(update)
    return web.Response()

# --- Aiohttp server ---
app = web.Application()
app.router.add_post(WEBHOOK_PATH, handle)
app.on_startup.append(on_startup)
app.on_shutdown.append(on_shutdown)

if __name__ == "__main__":
    logging.info("Запуск бота на Webhook...")
    web.run_app(app, host="0.0.0.0", port=PORT)
