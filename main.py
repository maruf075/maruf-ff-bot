import threading
import os
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- Flask Server Setup for Render Uptime ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Live 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# --- Database Setup ---
def init_db():
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            balance REAL DEFAULT 0.0
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            trx_id TEXT PRIMARY KEY,
            amount REAL,
            status TEXT DEFAULT 'pending'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            uid TEXT,
            days INTEGER,
            start_date TEXT,
            end_date TEXT
        )
    ''')
    conn.commit()
    conn.close()

def get_balance(user_id):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0.0

def add_balance(user_id, amount):
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO users (user_id, balance) VALUES (?, ?)
        ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?
    ''', (user_id, amount, amount))
    conn.commit()
    conn.close()

# API Configurations
API_KEY = "VALT2H"
API_URL = "https://YOUR-SMM-PROVIDER-DOMAIN.com/api/v2"  # আপনার API লিঙ্ক
SERVICE_ID_100 = "1"
DAILY_RATE = 8.0  # প্রতিদিনের লাইকের দাম (৮ টাকা)

# --- Telegram Bot Logic ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO users (user_id, balance) VALUES (?, 0.0)', (user_id,))
    conn.commit()
    conn.close()

    keyboard = [
        [InlineKeyboardButton("🔥 Free Fire Like", callback_data='ff_like'), InlineKeyboardButton("💎 Free Fire Diamond", callback_data='ff_diamond')],
        [InlineKeyboardButton("💳 My Balance", callback_data='balance'), InlineKeyboardButton("💵 Add Balance", callback_data='deposit')],
        [InlineKeyboardButton("📞 Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "স্বাগতম মারুফ টপ-আপ বটে! নিচের মেনু থেকে অপশন সিলেক্ট করুন:",
        reply_markup=reply_markup
    )

# /help Command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **বটের সকল কমান্ডের তালিকা:**\n\n"
        "• `/start` - বট চালু বা প্রারম্ভিক মেনু দেখতে\n"
        "• `/number` - পেমেন্ট নম্বর (বিকাশ ও নগদ) দেখতে\n"
        "• `/rate` - লাইক ও ডায়মন্ডের মূল্যের তালিকা দেখতে\n"
        "• `/balance` - ওয়ালেটে কত টাকা আছে দেখতে\n"
        "• `/verify <TrxID>` - পেমেন্ট ট্রানজেকশন আইডি সাবমিট ও ভেরিফাই করতে\n"
        "• `/add <UID> <দিন>` - নির্দিষ্ট দিনের জন্য লাইক প্যাকেজ কিনতে (যেমন: `/add 123456789 30D`)\n"
        "• `/usage` - ব্যবহৃত ও অবশিষ্টাংশের দিন দেখতে\n"
        "• `/help` - সকল কমান্ডের তালিকা দেখতে"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

# /number Command
async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🔷 **পেমেন্ট নম্বরসমূহ:**\n\n"
        "🔷 টাকা +1% সহ সেন্ড মানি করবেন।\n\n"
        "🅱 **Bkash:** `+8801618203922`\n"
        "🆖 **Nagad:** `+8801842408034`\n\n"
        "⏭️ লাস্ট ৩ ডিজিট নাম্বার বলবেন। (বাধ্যতামূলক)\n"
        "‼️ টাকা পাঠানোর ৫ মিনিটের ভিতরে জানাতে হবে।"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

# /rate Command
async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "(👍 ‿ 👍)✍️ **Like Prices**\n"
        "_______________________\n\n"
        "👉 Daily Like Package ⇨ 8.0 BDT / Day\n"
        "• `/add UID 1D` (১ দিনের জন্য)\n"
        "• `/add UID 30D` (৩০ দিনের জন্য)\n"
        "_______________________\n\n"
        "💎 **Diamond Prices**\n"
        "• 115 Diamond - 80 BDT\n"
        "• 240 Diamond - 160 BDT"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

# /balance Command
async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    await update.message.reply_text(f"💰 আপনার বর্তমান ওয়ালেট ব্যালেন্স: {bal} BDT")

# /verify Command
async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ অনুগ্রহ করে TrxID প্রদান করুন।\nউদাহরণ: `/verify BLK9823X1`", parse_mode='Markdown')
        return

    trx_id = context.args[0].strip().upper()
    
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM transactions WHERE trx_id = ?', (trx_id,))
    row = cursor.fetchone()

    if row:
        if row[0] == 'used':
            await update.message.reply_text("❌ এই TrxID-টি ইতিপূর্বে ব্যবহার করা হয়েছে।")
        else:
            await update.message.reply_text("✅ আপনার TrxID সফলভাবে ভেরিফাই হয়েছে!")
    else:
        cursor.execute('INSERT INTO transactions (trx_id, amount, status) VALUES (?, 0, "pending")', (trx_id,))
        conn.commit()
        await update.message.reply_text(f"⏳ আপনার TrxID `{trx_id}` ভেরিফিকেশনের জন্য গ্রহণ করা হয়েছে। অল্প সময়ের মধ্যেই ওয়ালেটে টাকা যোগ হয়ে যাবে।", parse_mode='Markdown')
    conn.close()

# /add UID 1D /add UID 30D Command
async def add_package_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়মে লিখুন:\n`/add 123456789 1D` বা `/add 123456789 30D`", parse_mode='Markdown')
        return

    uid = context.args[0]
    days_str = context.args[1].upper().replace("D", "")

    if not days_str.isdigit():
        await update.message.reply_text("❌ দিনের সংখ্যা সঠিক নয়! উদাহরণ: `1D`, `7D`, `30D`", parse_mode='Markdown')
        return

    days = int(days_str)
    total_cost = days * DAILY_RATE
    bal = get_balance(user_id)

    if bal < total_cost:
        await update.message.reply_text(f"❌ আপনার ওয়ালেটে পর্যাপ্ত ব্যালেন্স নেই!\n\nপ্রয়োজন: {total_cost} BDT\nবর্তমান ব্যালেন্স: {bal} BDT\n/number কমান্ড দিয়ে টাকা রিচার্জ করুন।")
        return

    start_date = datetime.now()
    end_date = start_date + timedelta(days=days)

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO subscriptions (user_id, uid, days, start_date, end_date)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, uid, days, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    add_balance(user_id, -total_cost)

    await update.message.reply_text(
        f"✅ **লাইক প্যাকেজ সফলভাবে অ্যাক্টিভ হয়েছে!**\n\n"
        f"🎮 UID: `{uid}`\n"
        f"📅 মেয়াদ: {days} দিন\n"
        f"💰 মোট খরচ: {total_cost} BDT\n"
        f"⏳ শেষ হওয়ার তারিখ: {end_date.strftime('%d-%m-%Y')}\n\n"
        f"ব্যবহার দেখতে `/usage` চাপুন।",
        parse_mode='Markdown'
    )

# /usage Command
async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT uid, days, start_date, end_date FROM subscriptions WHERE user_id = ? ORDER BY id DESC', (user_id,))
    subs = cursor.fetchall()
    conn.close()

    if not subs:
        await update.message.reply_text("❌ আপনার কোনো সক্রিয় লাইক প্যাকেজ পাওয়া যায়নি।")
        return

    msg = "📊 **আপনার লাইক প্যাকেজ ব্যবহারের বিবরণ:**\n\n"
    now = datetime.now()

    for sub in subs:
        uid, days, start_str, end_str = sub
        start_date = datetime.strptime(start_str, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")

        if now > end_date:
            status = "🔴 মেয়াদ শেষ"
            used_days = days
            remaining_days = 0
        else:
            status = "🟢 রানিং"
            used_days = (now - start_date).days
            if used_days < 0:
                used_days = 0
            remaining_days = (end_date - now).days + 1

        msg += (
            f"🎮 UID: `{uid}`\n"
            f"📌 স্ট্যাটাস: {status}\n"
            f"⏱️ ব্যবহৃত হয়েছে: {used_days} দিন\n"
            f"⏳ বাকি আছে: {remaining_days} দিন\n"
            f"_______________________\n"
        )

    await update.message.reply_text(msg, parse_mode='Markdown')

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data == 'ff_like':
        await rate_command(update, context)

    elif query.data == 'ff_diamond':
        await rate_command(update, context)

    elif query.data == 'balance':
        bal = get_balance(user_id)
        await query.message.reply_text(f"💰 আপনার বর্তমান ওয়ালেট ব্যালেন্স: {bal} BDT")

    elif query.data == 'deposit':
        await number_command(update, context)

    elif query.data == 'support':
        support_text = (
            "📞 সহায়তার জন্য যোগাযোগ করুন:\n\n"
            "💬 WhatsApp: wa.me/8801618203922 (01618203922)\n"
            "✈️ Telegram: @maruf3900"
        )
        await query.message.reply_text(support_text)

def run_bot():
    init_db()
    TOKEN = "8915748936:AAEJw_iwXbnuMQzrEIAJF163iRPe-30rlpY"
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("number", number_command))
    application.add_handler(CommandHandler("rate", rate_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("add", add_package_command))
    application.add_handler(CommandHandler("usage", usage_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    print("Telegram Bot Polling Started...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    threading.Thread(target=run_flask, daemon=True).start()
    run_bot()
    
