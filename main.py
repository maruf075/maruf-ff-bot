import os
import asyncio
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- আপনার নিজস্ব তথ্যসমূহ ---
ADMIN_IDS = [6347427263, 6992868111]  # <--- দুইটি আইডিই অ্যাডমিন হিসেবে সেট করা হলো
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"  
WHATSAPP_NUMBER = "+8801618203922"              

# ডেটাবেজের বদলে মেমোরি ব্যালেন্স স্টোরেজ
user_balances = {}

# --- Flask Server (Render Keep-Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live and Running 24/7!"

# --- Bot Command Menu Setup ---
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "বট চালু করুন"),
        BotCommand("help", "সাহায্য ও সাপোর্ট পেতে"),
        BotCommand("like", "লাইক অর্ডার করুন"),
        BotCommand("balance", "ব্যালেন্স চেক করুন"),
        BotCommand("rate", "লাইকের রেট লিস্ট"),
        BotCommand("number", "পেমেন্ট নম্বর"),
        BotCommand("usage", "ব্যবহারের নিয়ম"),
        BotCommand("admin", "অ্যাডমিন প্যানেল হেল্প"),
    ]
    await application.bot.set_my_commands(commands)

# --- ইউজার হ্যান্ডলারসমূহ ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

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
    help_text = (
        "🛠 **সাহায্য ও সাপোর্ট কেন্দ্র**\n\n"
        "যেকোনো সমস্যায় আমাদের সাথে যোগাযোগ করুন:\n"
        f"📱 **Telegram:** {TELEGRAM_SUPPORT_USERNAME}\n"
        f"💬 **WhatsApp:** {WHATSAPP_NUMBER}\n\n"
        "বটের ব্যবহারবিধি জানতে /usage লিখুন।"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_text = (
        "📊 **আমাদের বর্তমান লাইক রেট লিস্ট:**\n\n"
        "• ১০০ লাইক = ৭.৫ টাকা\n"
        "• ২০০ লাইক = ১৫ টাকা\n"
        "• ৫০০ লাইক = ৩৭.৫ টাকা\n"
        "• ১০০০ লাইক = ৭৫ টাকা"
    )
    await update.message.reply_text(rate_text, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)
    await update.message.reply_text(f"💳 আপনার বর্তমান ব্যালেন্স: {bal} BDT")

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("লাইক পেতে আপনার ফ্রি ফায়ার UID দিন। উদাহরণ: /like 123456789")

async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"টাকা পাঠাতে বিকাশ/নগদ (Personal) নম্বরে সেন্ড মানি করুন: {WHATSAPP_NUMBER}")

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("১. /start দিয়ে মেনু আনুন\n২. ব্যালেন্স যোগ করতে /number দেখুন\n৩. অর্ডার দিতে UID টাইপ করুন")

# --- অ্যাডমিন প্যানেল কমান্ডসমূহ ---
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ আপনি এই কমান্ড ব্যবহারের অধিকার রাখেন না।")
        return
    
    admin_msg = (
        "👑 **অ্যাডমিন কন্ট্রোল প্যানেল**\n\n"
        "১. ব্যালেন্স যোগ করতে: `/addbalance <User_ID> <Amount>`\n"
        "   উদাহরণ: `/addbalance 123456789 50`\n\n"
        "২. ব্যালেন্স কাটতে: `/cutbalance <User_ID> <Amount>`\n"
        "   উদাহরণ: `/cutbalance 123456789 20`\n\n"
        "৩. ইউজার ব্যালেন্স দেখতে: `/checkuser <User_ID>`\n"
        "   উদাহরণ: `/checkuser 123456789`"
    )
    await update.message.reply_text(admin_msg, parse_mode='Markdown')

async def admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        user_balances[target_id] = user_balances.get(target_id, 0.0) + amount
        await update.message.reply_text(f"✅ ইউজার `{target_id}` এর অ্যাকাউন্টে {amount} BDT যোগ করা হয়েছে!\nবর্তমান ব্যালেন্স: {user_balances[target_id]} BDT", parse_mode='Markdown')
        
        try:
            await context.bot.send_message(chat_id=target_id, text=f"🎉 আপনার অ্যাকাউন্টে {amount} BDT যোগ করা হয়েছে!\nবর্তমান ব্যালেন্স: {user_balances[target_id]} BDT")
        except:
            pass
    except Exception as e:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক ফরম্যাট: `/addbalance <User_ID> <Amount>`", parse_mode='Markdown')

async def admin_cut_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        user_balances[target_id] = max(0.0, user_balances.get(target_id, 0.0) - amount)
        await update.message.reply_text(f"✂️ ইউজার `{target_id}` এর অ্যাকাউন্ট থেকে {amount} BDT কেটে নেওয়া হয়েছে।\nবর্তমান ব্যালেন্স: {user_balances[target_id]} BDT", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক ফরম্যাট: `/cutbalance <User_ID> <Amount>`", parse_mode='Markdown')

async def admin_check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        target_id = int(context.args[0])
        bal = user_balances.get(target_id, 0.0)
        await update.message.reply_text(f"👤 **ইউজার ইনফো:**\nID: `{target_id}`\nব্যালেন্স: {bal} BDT", parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক ফরম্যাট: `/checkuser <User_ID>`", parse_mode='Markdown')

# Callback Button Handlers
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data == 'my_balance':
        bal = user_balances.get(user_id, 0.0)
        await query.edit_message_text(f"💳 আপনার বর্তমান ব্যালেন্স: {bal} BDT")
    elif query.data == 'add_balance':
        await query.edit_message_text("ব্যালেন্স যোগ করতে /number লিখে পেমেন্ট বিবরণ জেনে টাকা সেন্ড মানি করুন। তারপর অ্যাডমিনকে ট্রানজেকশন আইডি দিন।")
    elif query.data == 'support':
        support_msg = (
            "📞 **আমাদের কাস্টমার সাপোর্ট:**\n\n"
            f"• Telegram: {TELEGRAM_SUPPORT_USERNAME}\n"
            f"• WhatsApp: {WHATSAPP_NUMBER}"
        )
        await query.edit_message_text(support_msg, parse_mode='Markdown')
    elif query.data == 'ff_like':
        await query.edit_message_text("লাইকের সার্ভিস সিলেক্ট করেছেন। আপনার UID লিখে পাঠান।")
    else:
        await query.edit_message_text(f"আপনি নির্বাচন করেছেন: {query.data}")

# --- Main App Execution ---
async def main():
    TOKEN = "8915748936:AAEJw_iwXbnuMQzrEIAJF163iRPe-30rlpY"
    
    application = Application.builder().token(TOKEN).build()

    # User Command Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("rate", rate_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("like", like_command))
    application.add_handler(CommandHandler("number", number_command))
    application.add_handler(CommandHandler("usage", usage_command))

    # Admin Commands Registration
    application.add_handler(CommandHandler("admin", admin_help))
    application.add_handler(CommandHandler("addbalance", admin_add_balance))
    application.add_handler(CommandHandler("cutbalance", admin_cut_balance))
    application.add_handler(CommandHandler("checkuser", admin_check_user))

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
    
    print("Telegram Bot Started Successfully!")
    
    await application.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
        
