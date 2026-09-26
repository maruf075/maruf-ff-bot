import os
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Flask Server (Render Keep-Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live and Running 24/7!"

# --- Bot Command Menu Setup ---
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "বট চালু করুন"),
        BotCommand("help", "সাহায্য ও নির্দেশনা"),
        BotCommand("like", "লাইক অর্ডার করুন"),
        BotCommand("balance", "ব্যালেন্স চেক করুন"),
        BotCommand("rate", "রেট লিস্ট দেখুন"),
        BotCommand("number", "পেমেন্ট নম্বর দেখুন"),
        BotCommand("usage", "ব্যবহারের নিয়ম"),
        BotCommand("verify", "ট্রানজেকশন ভেরিফাই করুন"),
    ]
    await application.bot.set_my_commands(commands)

async def auto_like_scheduler(application):
    while True:
        await asyncio.sleep(60)

# --- All Command Handlers ---
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

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("লাইক সার্ভিস ব্যবহার করতে মেনু থেকে অপশন নির্বাচন করুন অথবা UID টাইপ করুন।")

async def add_package_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("প্যাকেজ যোগ করার আদেশ গৃহীত হয়েছে।")

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("সার্ভার সময় স্বাভাবিক রয়েছে।")

async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("টাকা রিচার্জ করতে দেওয়া নম্বরে সেন্ড মানি করুন (bKash/Nagad): 017XXXXXXXX")

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("বর্তমান রেট লিস্ট:\n- ১০০ লাইক = ১০ টাকা\n- ৫০০ লাইক = ৪৫ টাকা")

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("আপনার বর্তমান ব্যালেন্স: 0.0 BDT")

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ভেরিফিকেশন সম্পন্ন করার জন্য ট্রানজেকশন আইডি প্রদান করুন।")

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ব্যবহারের নিয়মাবলী:\n১. /start চাপুন\n২. ব্যালেন্স যোগ করুন\n৩. সার্ভিস সিলেক্ট করুন")

# Admin Commands
async def admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("অ্যাডমিন: ব্যালেন্স যোগ করা হয়েছে।")

async def admin_cut_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("অ্যাডমিন: ব্যালেন্স কাটা হয়েছে।")

async def admin_check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("অ্যাডমিন: ইউজার তথ্য প্রদর্শিত হচ্ছে।")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("অ্যাডমিন: ব্রডকাস্ট মেসেজ পাঠানো হয়েছে।")

# Callback Button Handlers
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'my_balance':
        await query.edit_message_text("আপনার বর্তমান ব্যালেন্স: 0.0 BDT")
    elif query.data == 'add_balance':
        await query.edit_message_text("ব্যালেন্স যোগ করতে /number কমান্ড ব্যবহার করে পেমেন্ট করুন।")
    elif query.data == 'support':
        await query.edit_message_text("সাপোর্টের জন্য অ্যাডমিন আইডিতে মেসেজ দিন: @YourAdminUsername")
    else:
        await query.edit_message_text(f"আপনি নির্বাচন করেছেন: {query.data}")

# --- Main App Execution ---
async def main():
    TOKEN = "8915748936:AAEJw_iwXbnuMQzrEIAJF163iRPe-30rlpY"
    
    application = Application.builder().token(TOKEN).build()

    # User Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("like", like_command))
    application.add_handler(CommandHandler("add", add_package_command))
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("number", number_command))
    application.add_handler(CommandHandler("rate", rate_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("usage", usage_command))
    
    # Admin Command Handlers
    application.add_handler(CommandHandler("addbalance", admin_add_balance))
    application.add_handler(CommandHandler("cutbalance", admin_cut_balance))
    application.add_handler(CommandHandler("checkuser", admin_check_user))
    application.add_handler(CommandHandler("broadcast", admin_broadcast))

    # Inline Buttons Handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start Flask Server inside Event Loop
    port = int(os.environ.get("PORT", 10000))
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: app.run(host='0.0.0.0', port=port, use_reloader=False))

    # Initialize Bot & Polling
    await application.initialize()
    await application.start()
    await set_bot_commands(application)
    asyncio.create_task(auto_like_scheduler(application))
    
    print("Telegram Bot Started Successfully!")
    
    await application.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
                         
