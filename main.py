import os
import asyncio
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- আপনার নতুন বট টোকেন ---
BOT_TOKEN = "8915748936:AAGPXAt0h-7tWOPpumGWrzoYejXf3xRPHJQ"

# --- আপনার নিজস্ব তথ্যসমূহ ---
ADMIN_IDS = [6347427263, 6992868111]  
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"  
WHATSAPP_NUMBER = "+8801618203922"              

# ইন-মেমোরি ডেটাবেজ (ব্যালেন্স ও সাবস্ক্রিপশন)
user_balances = {}
active_subscriptions = {}

# --- Flask Server (Render Keep-Alive) ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live and Running 24/7!"

# --- Bot Command Menu Setup ---
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "বট চালু করুন"),
        BotCommand("help", "সকল কমান্ডের তালিকা"),
        BotCommand("support", "সাপোর্ট তথ্য"),
        BotCommand("number", "পেমেন্ট নম্বর"),
        BotCommand("rate", "লাইকের রেট লিস্ট"),
        BotCommand("balance", "ওয়ালেট ব্যালেন্স"),
        BotCommand("verify", "ট্রানজেকশন ভেরিফাই করুন"),
        BotCommand("add", "লাইক প্যাকেজ যোগ করুন"),
        BotCommand("usage", "লাইক ব্যবহারের হিসেব"),
        BotCommand("time", "অটো টাইম সেট করুন"),
        BotCommand("like", "ইনস্ট্যান্ট ম্যানুয়াল লাইক"),
        BotCommand("admin", "অ্যাডমিন প্যানেল"),
    ]
    await application.bot.set_my_commands(commands)

# --- ইউজার কমান্ডসমূহ ---
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
    await update.message.reply_text("স্বাগতম মারুফ টপ-আপ বটে! সকল কমান্ড একসাথে দেখতে /help টাইপ করুন।", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📜 **বটের সকল কমান্ডের তালিকা:**\n\n"
        "• /help - সকল কমান্ডের তালিকা দেখাবে\n"
        "• /support - কাস্টমার সাপোর্ট তথ্য দেখাবে\n"
        "• /number - বিকাশ/নগদ পেমেন্ট নম্বর\n"
        "• /rate - লাইকের অফার ও দামের তালিকা\n"
        "• /balance - ওয়ালেটের বর্তমান ব্যালেন্স\n"
        "• /verify `[TrxID]` - টাকা জমা দিয়ে ব্যালেন্স যুক্ত করুন\n"
        "• /add `[UID] [Likes] [Days]` - অটো-লাইক প্যাকেজ সাবস্ক্রাইব করুন\n"
        "• /time `[HH:MM]` - প্রতিদিন অটো-লাইক যাওয়ার সময় সেট করুন\n"
        "• /like `[UID] [Likes]` - ম্যানুয়ালি ইনস্ট্যান্ট লাইক নিন\n"
        "• /usage - আপনার ব্যবহৃত ও অবশিষ্ট লাইকের হিসেব\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    support_msg = (
        "📞 **আমাদের কাস্টমার সাপোর্ট:**\n\n"
        f"• **Telegram:** {TELEGRAM_SUPPORT_USERNAME}\n"
        f"• **WhatsApp:** {WHATSAPP_NUMBER}"
    )
    await update.message.reply_text(support_msg, parse_mode='Markdown')

async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"💵 টাকা পাঠাতে বিকাশ/নগদ (Personal) নম্বরে সেন্ড মানি করুন:\n`{WHATSAPP_NUMBER}`", parse_mode='Markdown')

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rate_text = (
        "📊 **আমাদের বর্তমান লাইক রেট লিস্ট:**\n\n"
        "• ১০০ লাইক = ৭.৫ টাকা\n"
        "• ২০০ লাইক = ১৫ টাকা\n"
        "• ৫০০ লাইক = ৩৭.৫ টাকা\n"
        "• ১০০০ লাইক = ৭৫ টাকা\n\n"
        "**দৈনিক প্যাকেজ (Subscriptions):**\n"
        "• ১০০ লাইক (১ দিন) = ৭.৫ টাকা | (৩০ দিন) = ২২৫ টাকা\n"
        "• ২০০ লাইক (১ দিন) = ১৫ টাকা | (৩০ দিন) = ৪৫০ টাকা"
    )
    await update.message.reply_text(rate_text, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)
    await update.message.reply_text(f"💳 আপনার ওয়ালেটে আছে: **{bal} BDT**", parse_mode='Markdown')

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ট্রানজেকশন আইডি প্রদান করুন।\nউদাহরণ: `/verify 9J7X8K2L`", parse_mode='Markdown')
        return
    trx_id = context.args[0]
    await update.message.reply_text(f"⏳ আপনার ট্রানজেকশন আইডি `{trx_id}` চেক করা হচ্ছে। সঠিক থাকলে কিছুক্ষণের মধ্যে ওয়ালেটে টাকা যুক্ত হবে।", parse_mode='Markdown')

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = context.args[0]
        likes = int(context.args[1])
        days_str = context.args[2].upper().replace("D", "")
        days = int(days_str)

        user_id = update.effective_user.id
        end_date = datetime.now() + timedelta(days=days)

        active_subscriptions[user_id] = {
            "uid": uid,
            "daily_likes": likes,
            "start_date": datetime.now(),
            "end_date": end_date,
            "total_days": days,
            "used_likes": 0,
            "auto_time": "12:00"
        }
        await update.message.reply_text(f"✅ সফলভাবে **{days} দিনের** লাইক প্যাকেজ যোগ করা হয়েছে!\n🎯 **UID:** {uid}\n🔥 **দৈনিক লাইক:** {likes}", parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/add [UID] [Likes] [Days]`\nউদাহরণ: `/add 12345678 100 30D`", parse_mode='Markdown')

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_subscriptions:
        await update.message.reply_text("❌ আপনার কোনো সক্রিয় লাইক প্যাকেজ নেই।")
        return

    sub = active_subscriptions[user_id]
    now = datetime.now()
    days_used = (now - sub["start_date"]).days
    days_left = max(0, (sub["end_date"] - now).days)
    
    total_likes_promised = sub["daily_likes"] * sub["total_days"]
    likes_used = sub["used_likes"]
    likes_remaining = max(0, total_likes_promised - likes_used)

    msg = (
        "📊 **আপনার প্যাকেজ ব্যবহার বিবরণ:**\n\n"
        f"🎯 **Target UID:** `{sub['uid']}`\n"
        f"📅 **ব্যবহৃত দিন:** {days_used} দিন\n"
        f"⏳ **বাকি আছে:** {days_left} দিন\n"
        f"👍 **ব্যবহৃত লাইক:** {likes_used} টি\n"
        f"🔹 **অবশিষ্ট লাইক:** {likes_remaining} টি\n"
        f"⏰ **অটো টাইম:** প্রতিদিন {sub['auto_time']} টায়"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_subscriptions:
        await update.message.reply_text("❌ আপনার কোনো সক্রিয় লাইক প্যাকেজ নেই।")
        return

    if not context.args:
        await update.message.reply_text("❌ সময় প্রদান করুন।\nউদাহরণ: `/time 14:30` (২৪ ঘণ্টার ফরম্যাটে)", parse_mode='Markdown')
        return

    set_time = context.args[0]
    active_subscriptions[user_id]["auto_time"] = set_time
    await update.message.reply_text(f"⏰ অটো লাইকের সময় সফলভাবে **{set_time}** টায় নির্ধারণ করা হয়েছে।", parse_mode='Markdown')

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = context.args[0]
        likes = int(context.args[1])
        await update.message.reply_text(f"🚀 UID: `{uid}` এ **{likes}** টি ইনস্ট্যান্ট লাইক পাঠানো শুরু হয়েছে!", parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/like [UID] [Amount]`\nউদাহরণ: `/like 12345678 100`", parse_mode='Markdown')

# --- অ্যাডমিন কমান্ডসমূহ ---
async def admin_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    admin_msg = (
        "👑 **অ্যাডমিন কন্ট্রোল প্যানেল**\n\n"
        "• `/addbalance <User_ID> <Amount>`\n"
        "• `/cutbalance <User_ID> <Amount>`\n"
        "• `/checkuser <User_ID>`"
    )
    await update.message.reply_text(admin_msg, parse_mode='Markdown')

async def admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        user_balances[target_id] = user_balances.get(target_id, 0.0) + amount
        await update.message.reply_text(f"✅ ইউজার `{target_id}` এর অ্যাকাউন্টে {amount} BDT যোগ করা হয়েছে!", parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ ফরম্যাট: `/addbalance <User_ID> <Amount>`", parse_mode='Markdown')

# --- Callback Button Handler ---
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()
    
    if query.data == 'my_balance':
        bal = user_balances.get(user_id, 0.0)
        await query.edit_message_text(f"💳 আপনার ওয়ালেটে আছে: **{bal} BDT**", parse_mode='Markdown')
    elif query.data == 'add_balance':
        await query.edit_message_text("ব্যালেন্স যোগ করতে /number থেকে নম্বর নিয়ে সেন্ড মানি করুন এবং /verify [TrxID] প্রদান করুন।")
    elif query.data == 'support':
        await query.edit_message_text(f"📞 Support:\nTelegram: {TELEGRAM_SUPPORT_USERNAME}\nWhatsApp: {WHATSAPP_NUMBER}")

# --- Main Application Execution ---
async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    # User Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("number", number_command))
    application.add_handler(CommandHandler("rate", rate_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("usage", usage_command))
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("like", like_command))

    # Admin Handlers
    application.add_handler(CommandHandler("admin", admin_help))
    application.add_handler(CommandHandler("addbalance", admin_add_balance))

    # Inline Buttons
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
                          
