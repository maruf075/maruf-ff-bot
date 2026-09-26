import threading
import os
import requests
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask Server Setup for Render Uptime
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Live 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# API Configurations
API_KEY = "VALT2H"
API_URL = "https://YOUR-SMM-PROVIDER-DOMAIN.com/api/v2"  # আপনার API লিঙ্ক এখানে বসান
SERVICE_ID_100 = "1"  # ১০০ লাইকের সার্ভিস আইডি
SERVICE_ID_200 = "2"  # ২০০ লাইকের সার্ভিস আইডি

# --- Telegram Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🔥 Free Fire Like", callback_data='ff_like'), InlineKeyboardButton("💎 Free Fire Diamond", callback_data='ff_diamond')],
        [InlineKeyboardButton("💳 My Balance", callback_data='balance'), InlineKeyboardButton("📞 Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "স্বাগতম মারুফ টপ-আপ বটে! নিচের মেনু থেকে অপশন সিলেক্ট করুন:",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'ff_like':
        text = (
            "(👍 ‿ 👍)✍️ Like Prices\n"
            "_______________________\n\n"
            "👉 100 Likes ⇨ 8.0 BDT\n"
            "👉 200 Likes ⇨ 15.0 BDT\n"
            "_______________________\n\n"
            "কমান্ডের মাধ্যমে লাইক অর্ডার করুন:\n"
            "• `/like UID` -> 100 Likes\n"
            "• `/like200 UID` -> 200 Likes"
        )
        await query.message.reply_text(text)

    elif query.data == 'ff_diamond':
        text = (
            "💎 Free Fire Diamond Price:\n"
            "• 115 Diamond - 80 BDT\n"
            "• 240 Diamond - 160 BDT\n\n"
            "অর্ডার করতে আপনার UID সহ যোগাযোগ করুন।"
        )
        await query.message.reply_text(text)

    elif query.data == 'balance':
        await query.message.reply_text("💰 আপনার ব্যালেন্স: 0 BDT\n\nটাকা রিচার্জ করতে অ্যাডমিনকে নক দিন।")

    elif query.data == 'support':
        support_text = (
            "📞 **সহায়তার জন্য যোগাযোগ করুন:**\n\n"
            "💬 WhatsApp: wa.me/8801618203922 (01618203922)\n"
            "✈️ Telegram: @maruf3900"
        )
        await query.message.reply_text(support_text, parse_mode='Markdown')

# 100 Likes Command (/like UID)
async def like100_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ অনুগ্রহ করে UID প্রদান করুন।\nউদাহরণ: `/like 123456789`", parse_mode='Markdown')
        return

    uid = context.args[0]
    await update.message.reply_text(f"⏳ UID: {uid}-এ 100 লাইকের রিকোয়েস্ট প্রসেস করা হচ্ছে...")

    payload = {
        'key': API_KEY,
        'action': 'add',
        'service': SERVICE_ID_100,
        'link': uid,
        'quantity': 100
    }
    
    try:
        response = requests.post(API_URL, data=payload).json()
        if "order" in response:
            await update.message.reply_text(f"✅ অর্ডার সফল হয়েছে!\nOrder ID: {response['order']}\nUID: {uid}")
        else:
            await update.message.reply_text(f"❌ অর্ডার ব্যর্থ হয়েছে। কারণ: {response.get('error', 'অজানা সমস্যা')}")
    except Exception as e:
        await update.message.reply_text("❌ সার্ভার প্রোভাইডারের সাথে সংযোগ করা যাচ্ছে না।")

def run_bot():
    TOKEN = "8915748936:AAEJw_iwXbnuMQzrEIAJF163iRPe-30rlpY"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("like", like100_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Telegram Bot Polling Started...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
