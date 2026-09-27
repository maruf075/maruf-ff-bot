import os
import asyncio
import threading
import requests
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8915748936:AAGPXAt0h-7tWOPpumGWrzoYejXf3xRPHJQ"
LIKE_API_KEY = "VALT2H"

ADMIN_IDS = [6347427263, 6992868111]  
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"  
WHATSAPP_NUMBER = "+8801618203922"              

user_balances = {}
active_subscriptions = {}
user_api_keys = {}

item_prices = {
    "d25": 20, "d50": 35, "d115": 80, "d240": 160, "d610": 400,
    "weekly": 160, "monthly": 800, "like_7days": 50, "like_30days": 180
}

vouchers_stock = {
    "25": [], "50": [], "115": [], "240": [], "610": [], "weekly": [], "monthly": []
}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live and Running 24/7!"

def send_like_request(api_key, uid):
    endpoints = [
        f"https://key.like.mlbbshop.com/like?key={api_key}&uid={uid}",
        f"https://freefirelike.com/api/like?key={api_key}&uid={uid}",
        f"https://buykey.freefirelike.com/like?key={api_key}&uid={uid}"
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json(), 200
        except Exception:
            continue
    return None, 404

async def set_bot_commands(application):
    commands = [
        BotCommand("start", "বট চালু করুন"),
        BotCommand("help", "সকল কমান্ডের তালিকা"),
        BotCommand("key", "API Key সেট করুন"),
        BotCommand("support", "সাপোর্ট তথ্য"),
        BotCommand("number", "পেমেন্ট নম্বর"),
        BotCommand("rate", "লাইকের রেট লিস্ট"),
        BotCommand("balance", "ওয়ালেট ব্যালেন্স"),
        BotCommand("verify", "ট্রানজেকশন ভেরিফাই করুন"),
        BotCommand("add", "লাইক প্যাকেজ যোগ করুন"),
        BotCommand("delete", "শেডিউল ডিলিট করুন"),
        BotCommand("usage", "API Usage বিবরণ"),
        BotCommand("list", "অ্যাক্টিভ শেডিউল লিস্ট"),
        BotCommand("time", "অটো টাইম সেট করুন"),
        BotCommand("like", "ইনস্ট্যান্ট লাইক পাঠান"),
        BotCommand("stock", "UniPin ভাউচার স্টক দেখুন"),
        BotCommand("tp", "ডায়মন্ড ও মেম্বারশিপ টপ-আপ করুন"),
        BotCommand("topup", "ডায়মন্ড ও মেম্বারশিপ টপ-আপ করুন"),
        BotCommand("addvoucher", "[Admin] ভাউচার এড করুন"),
        BotCommand("setrate", "[Admin] দাম পরিবর্তন করুন"),
        BotCommand("admin", "অ্যাডমিন প্যানেল"),
    ]
    await application.bot.set_my_commands(commands)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    keyboard = [
        [InlineKeyboardButton("🔥 Free Fire Like", callback_data='ff_like'),
         InlineKeyboardButton("💎 Free Fire Diamond", callback_data='ff_diamond')],
        [InlineKeyboardButton("💳 My Balance", callback_data='my_balance'),
         InlineKeyboardButton("📦 Stock Check", callback_data='check_stock')],
        [InlineKeyboardButton("📞 Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 স্বাগতম মারুফ লাইক ও টপ-আপ বটে! সকল কমান্ড একসাথে দেখতে /help টাইপ করুন।", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📜 **বটের সকল কমান্ডের তালিকা:**\n\n"
        "• /key `[KEY]` - API Key সেট করুন\n"
        "• /help - সকল কমান্ডের তালিকা देखাবে\n"
        "• /support - কাস্টমার সাপোর্ট তথ্য\n"
        "• /number - বিকাশ/নগদ পেমেন্ট নম্বর\n"
        "• /rate - লাইক ও ডায়মন্ডের দামের তালিকা\n"
        "• /balance - ওয়ালেটের বর্তমান ব্যালেন্স\n"
        "• /stock - UniPin ভাউচারের বর্তমান স্টক দেখুন\n"
        "• /tp `[UID] [Package]` - ডায়মন্ড/মেম্বারশিপ টপ-আপ করুন\n"
        "• /verify `[TrxID]` - টাকা জমা দিয়ে ব্যালেন্স যুক্ত করুন\n"
        "• /add `[UID] [Likes] [Days]` - অটো-লাইক প্যাকেজ যোগ করুন\n"
        "• /delete `[Schedule_ID]` - রানিং শেডিউল ডিলিট করুন\n"
        "• /usage - API Key ব্যবহারের বিবরণ\n"
        "• /list - অ্যাক্টিভ শেডিউলের তালিকা\n"
        "• /time `[HH:MM]` - অটো-লাইকের সময় সেট করুন\n"
        "• /like `[UID]` - ইনস্ট্যান্ট লাইক পাঠান\n\n"
        "⚙️ **অ্যাডমিন কমান্ডসমূহ:**\n"
        "• /addvoucher `[Pkg] [Code]` - স্টক যোগ করুন\n"
        "• /setrate `[Type] [Pkg] [Price]` - দাম পরিবর্তন করুন\n"
        "• /admin - অ্যাডমিন কন্ট্রোল প্যানেল\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

def run_telegram_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    
    loop.run_until_complete(set_bot_commands(application))
    application.run_polling(drop_pending_updates=True, stop_signals=None)

# Telegram Bot in background thread
bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
bot_thread.start()

# Flask Web Server
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
            
