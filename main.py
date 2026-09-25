import os
import logging
from threading import Thread
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask Web Server setup for Render Keep-Alive
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

TOKEN ="8915748936:AAEJw_iwXbnuMQzrEIAJF163iRPe-30rlpY"


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [
            InlineKeyboardButton("🔥 Free Fire Like", callback_data='like_sell'),
            InlineKeyboardButton("💎 Free Fire Diamond", callback_data='diamond_sell')
        ],
        [
            InlineKeyboardButton("💳 My Balance", callback_data='balance'),
            InlineKeyboardButton("📞 Support", callback_data='support')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('স্বাগতম মারুফ টপ-আপ বটে! নিচের মেনু থেকে অপশন সিলেক্ট করুন:', reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'like_sell':
        await query.message.reply_text("🔥 Free Fire Like Price:\n• 1000 Likes - 50 BDT\n• 2000 Likes - 90 BDT\n\nঅর্ডার করতে আপনার UID সহ যোগাযোগ করুন।")
    elif query.data == 'diamond_sell':
        await query.message.reply_text("💎 Free Fire Diamond Price:\n• 115 Diamond - 80 BDT\n• 240 Diamond - 160 BDT\n\nঅর্ডার করতে আপনার UID পাঠান।")
    elif query.data == 'balance':
        await query.message.reply_text("💰 আপনার ব্যালেন্স: 0 BDT")
    elif query.data == 'support':
        await query.message.reply_text("📞 সহায়তার জন্য যোগাযোগ করুন: @marufbhai075")

def main() -> None:
    keep_alive()  # Start the Web Server
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.run_polling()

if __name__ == '__main__':
    main()
    
