import os
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Flask Web Server (Render IP Check) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live and running 24/7!"

# --- Bot Commands Setup ---
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "বট চালু করুন"),
        BotCommand("help", "সাহায্য ও নির্দেশনা"),
        BotCommand("like", "লাইক অর্ডার করুন"),
        BotCommand("balance", "ব্যালেন্স চেক করুন"),
    ]
    await application.bot.set_my_commands(commands)

async def auto_like_scheduler(application):
    while True:
        await asyncio.sleep(60)

# --- Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Free Fire Like", callback_data='ff_like'),
         InlineKeyboardButton("💎 Free Fire Diamond", callback_data='ff_diamond')],
        [InlineKeyboardButton("💳 My Balance", callback_data='my_balance'),
         InlineKeyboardButton("💵 Add Balance", callback_data='add_balance')],
        [InlineKeyboardButton("📞 Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("স্বাগতম মারুফ টপ-আপ বটে! নিচের মেনু থেকে অপশন সিলেক্ট করুন:", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("সাহায্যের জন্য অ্যাডমিনের সাথে যোগাযোগ করুন অথবা /start টাইপ করুন।")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'my_balance':
        await query.edit_message_text("আপনার বর্তমান ব্যালেন্স: 0.0 BDT")
    else:
        await query.edit_message_text(f"আপনি নির্বাচন করেছেন: {query.data}")

# --- Main App Execution ---
async def main():
    TOKEN = "8915748936:AAEJw_iwXbnuMQzrEIAJF163iRPe-30rlpY"
    
    # Initialize Telegram Application
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start Flask Server inside Event Loop
    port = int(os.environ.get("PORT", 10000))
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: app.run(host='0.0.0.0', port=port, use_reloader=False))

    # Initialize Bot & Polling natively
    await application.initialize()
    await application.start()
    await set_bot_commands(application)
    asyncio.create_task(auto_like_scheduler(application))
    
    print("Telegram Bot Started Successfully!")
    
    # Start polling safely on main loop
    await application.updater.start_polling(drop_pending_updates=True)
    
    # Keep application alive
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
