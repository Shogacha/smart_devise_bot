import os
from dotenv import load_dotenv
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import logging

from twilio.rest import Client

# Токен Telegram бота
TOKEN = os.getenv("TELEGRAM_TOKEN")

# Каталог товаров
catalogs = {
    "convenience": [
        ("Датчик движения", "rC:/Users/dsod1/Desktop/12.jpg"),
        ("Умная розетка", "rC:/Users/dsod1/Desktop/13.jpg"),
        ("Светильник с датчиком", "rC:/Users/dsod1/Desktop/14.jpg"),
    ],
    "security": [
        ("Умный замок", "rC:/Users/dsod1/Desktop/15.jpg"),
        ("Камера наблюдения", "rC:/Users/dsod1/Desktop/16.jpg"),
        ("Сигнализация", "rC:/Users/dsod1/Desktop/17.jpg"),
    ]
}

user_data = {}

# Twilio настройки
account_sid = os.getenv("TWILIO_ACCOUNT_SID")
auth_token = os.getenv("TWILIO_AUTH_TOKEN")

TWILIO_WHATSAPP_NUMBER = "whatsapp:+19787337969"  # sandbox номер Twilio
YOUR_WHATSAPP_NUMBER = "whatsapp:+992005997884"  # номер, на который будут приходить заказы

twilio_client = Client(account_sid, auth_token)

def send_order_to_whatsapp(order_text: str):
    message = twilio_client.messages.create(
        body=order_text,
        from_=TWILIO_WHATSAPP_NUMBER,
        to=YOUR_WHATSAPP_NUMBER
    )
    print("Отправлено в WhatsApp:", message.sid)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Удобство", callback_data="category:convenience")],
        [InlineKeyboardButton("Надежность", callback_data="category:security")]
    ]
    await update.message.reply_text("Выберите категорию:", reply_markup=InlineKeyboardMarkup(keyboard))

async def category_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.split(":")[1]
    keyboard = [
        [InlineKeyboardButton(item[0], callback_data=f"item:{item[0]}")] for item in catalogs[category]
    ]
    user_data[query.from_user.id] = {"category": category}
    await query.edit_message_text("Выберите товар:", reply_markup=InlineKeyboardMarkup(keyboard))

async def item_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    item = query.data.split(":")[1]
    user_data[query.from_user.id]["item"] = item
    await query.edit_message_text(f"Вы выбрали: {item}\nНапишите ваше имя и адрес доставки в чат.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id in user_data and "item" in user_data[user_id]:
        info = update.message.text
        item = user_data[user_id]["item"]
        order_text = f"Заказ: {item}\nДанные клиента: {info}"
        send_order_to_whatsapp(order_text)
        await update.message.reply_text("Ваш заказ принят! Мы свяжемся с вами в WhatsApp.")
        del user_data[user_id]
    else:
        await update.message.reply_text("Пожалуйста, начните с команды /start.")

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(category_selected, pattern="^category:"))
    app.add_handler(CallbackQueryHandler(item_selected, pattern="^item:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
