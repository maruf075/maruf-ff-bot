import asyncio
import os
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- ADMIN CONFIGURATION ---
ADMIN_IDS = [6347427263, 6992868111]

# --- Flask Server Setup for Render Uptime ---
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Running Live 24/7!"

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
            end_date TEXT,
            preferred_time TEXT DEFAULT '12:00',
            last_sent_date TEXT DEFAULT ''
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

# --- API Configurations ---
API_KEY = "VALT2H"
API_URL = "https://api.your-smm-panel.com/api/v2"  # <--- আপনার SMM প্যানেলের মূল API লিংকটি এখানে বসান
SERVICE_ID_100 = "1"
DAILY_RATE = 8.0  # ১০০ লাইকের দাম ৮ টাকা

# --- Async Auto Like Scheduler Loop ---
async def auto_like_scheduler(bot_application):
    while True:
        try:
            now = datetime.now()
            current_time_str = now.strftime("%H:%M")
            current_date_str = now.strftime("%Y-%m-%d")

            conn = sqlite3.connect('bot_database.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, user_id, uid, end_date, preferred_time, last_sent_date 
                FROM subscriptions 
                WHERE preferred_time = ? AND last_sent_date != ?
            ''', (current_time_str, current_date_str))
            
            subs = cursor.fetchall()

            for sub in subs:
                sub_id, user_id, uid, end_str, pref_time, last_sent = sub
                end_date = datetime.strptime(end_str, "%Y-%m-%d %H:%M:%S")

                if now <= end_date:
                    payload = {
                        'key': API_KEY,
                        'action': 'add',
                        'service': SERVICE_ID_100,
                        'link': uid,
                        'quantity': 100
                    }
                    try:
                        res = requests.post(API_URL, data=payload).json()
                        if "order" in res:
                            cursor.execute('UPDATE subscriptions SET last_sent_date = ? WHERE id = ?', (current_date_str, sub_id))
                            conn.commit()
                            await bot_application.bot.send_message(
                                chat_id=user_id,
                                text=f"🤖 **অটো-লাইক আপডেট!**\n\n🎮 UID: `{uid}`-এ নির্ধারিত সময় ({pref_time})-এ ১০০ লাইক সফলভাবে পাঠানো হয়েছে।",
                                parse_mode='Markdown'
                            )
                    except Exception as e:
                        print(f"Auto like failed for UID {uid}: {e}")

            conn.close()
        except Exception as e:
            print(f"Scheduler error: {e}")
        
        await asyncio.sleep(60)

# --- Set Telegram Menu Commands Automatically ---
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "বট চালু করতে"),
        BotCommand("help", "সাহায্য ও কমান্ড তালিকা"),
        BotCommand("like", "ইনস্ট্যান্ট ১০০ লাইক নিতে"),
        BotCommand("add", "লাইক প্যাকেজ সাবস্ক্রাইব করতে"),
        BotCommand("time", "ডেইলি অটো লাইকের সময় সেট করতে"),
        BotCommand("number", "পেমেন্ট নম্বরসমূহ দেখতে"),
        BotCommand("rate", "লাইক ও ডায়মন্ডের দাম জানতে"),
        BotCommand("balance", "ওয়ালেট ব্যালেন্স দেখতে"),
        BotCommand("verify", "পেমেন্ট ট্রানজেকশন ভেরিফাই করতে"),
        BotCommand("usage", "প্যাকেজ ব্যবহারের তথ্য দেখতে")
    ]
    await application.bot.set_my_commands(commands)

# --- Bot Command Handlers ---
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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🤖 **বটের সকল কমান্ডের তালিকা:**\n\n"
        "• /start - বট চালু বা প্রারম্ভিক মেনু\n"
        "• /like `<UID>` - ইনস্ট্যান্ট ১০০ লাইক নিতে (দাম: ৮ BDT)\n"
        "• /add `<UID>` `<দিন>` - নির্দিষ্ট দিনের প্যাকেজ কিনতে (যেমন: `/add 123456789 30D`)\n"
        "• /time `<UID>` `<HH:MM>` - অটো লাইকের সময় সেট করতে (যেমন: `/time 123456789 21:30`)\n"
        "• /number - পেমেন্ট নম্বর (বিকাশ ও নগদ) দেখতে\n"
        "• /rate - লাইক ও ডায়মন্ডের মূল্যের তালিকা\n"
        "• /balance - ওয়ালেটে কত টাকা আছে দেখতে\n"
        "• /verify `<TrxID>` - পেমেন্ট ভেরিফাই করে ব্যালেন্স যোগ করতে\n"
        "• /usage - সাবস্ক্রিপশন ব্যবহারের ইতিহাস দেখতে\n"
        "• /help - সহায়তার জন্য নির্দেশিকা"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    
    if not context.args:
        await update.message.reply_text("❌ অনুগ্রহ করে UID প্রদান করুন।\nউদাহরণ: `/like 123456789`", parse_mode='Markdown')
        return

    if bal < DAILY_RATE:
        await update.message.reply_text(f"❌ আপনার ওয়ালেটে পর্যাপ্ত ব্যালেন্স নেই!\n\nপ্রয়োজন: {DAILY_RATE} BDT\nবর্তমান ব্যালেন্স: {bal} BDT\n/number কমান্ড দিয়ে টাকা রিচার্জ করুন।")
        return

    uid = context.args[0]
    await update.message.reply_text(f"⏳ UID: `{uid}` -এ ১০০ লাইকের ইনস্ট্যান্ট রিকোয়েস্ট প্রসেস করা হচ্ছে...", parse_mode='Markdown')

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
            add_balance(user_id, -DAILY_RATE)
            new_bal = get_balance(user_id)
            await update.message.reply_text(
                f"✅ **ইনস্ট্যান্ট লাইক অর্ডার সফল হয়েছে!**\n\n"
                f"🆔 Order ID: `{response['order']}`\n"
                f"🎮 UID: `{uid}`\n"
                f"💰 কাটা হয়েছে: {DAILY_RATE} BDT\n"
                f"💳 বর্তমান ব্যালেন্স: {new_bal} BDT",
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(f"❌ অর্ডার ব্যর্থ হয়েছে। কারণ: {response.get('error', 'অজানা সমস্যা')}")
    except Exception as e:
        await update.message.reply_text("❌ সার্ভার প্রোভাইডারের সাথে সংযোগ করা যাচ্ছে না।")

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
        INSERT INTO subscriptions (user_id, uid, days, start_date, end_date, preferred_time)
        VALUES (?, ?, ?, ?, ?, '12:00')
    ''', (user_id, uid, days, start_date.strftime("%Y-%m-%d %H:%M:%S"), end_date.strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    add_balance(user_id, -total_cost)

    await update.message.reply_text(
        f"✅ **লাইক প্যাকেজ সফলভাবে অ্যাক্টিভ হয়েছে!**\n\n"
        f"🎮 UID: `{uid}`\n"
        f"📅 মেয়াদ: {days} দিন\n"
        f"💰 মোট খরচ: {total_cost} BDT\n"
        f"⏰ অটো-লাইক টাইম: `12:00` (ডিফল্ট)\n"
        f"⏳ শেষ হওয়ার তারিখ: {end_date.strftime('%d-%m-%Y')}\n\n"
        f"💡 সময় পরিবর্তন করতে লিখুন: `/time {uid} 21:30` (আপনার পছন্দমতো সময়)",
        parse_mode='Markdown'
    )

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if len(context.args) < 2:
        await update.message.reply_text("❌ সঠিক নিয়মে লিখুন:\n`/time <UID> <HH:MM>`\n\nউদাহরণ (রাত ৯:৩০ টা): `/time 123456789 21:30`", parse_mode='Markdown')
        return

    uid = context.args[0]
    time_str = context.args[1]

    try:
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text("❌ ভুল টাইম ফরম্যাট! ২৪ ঘণ্টার সময় ফরম্যাট ব্যবহার করুন (যেমন: `09:00`, `15:30`, `21:00`)", parse_mode='Markdown')
        return

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM subscriptions WHERE user_id = ? AND uid = ? ORDER BY id DESC LIMIT 1', (user_id, uid))
    row = cursor.fetchone()

    if row:
        cursor.execute('UPDATE subscriptions SET preferred_time = ? WHERE id = ?', (time_str, row[0]))
        conn.commit()
        await update.message.reply_text(f"⏰ **সময় সফলভাবে আপডেট হয়েছে!**\n\n🎮 UID: `{uid}`\n⏰ এখন প্রতিদিন ঠিক `{time_str}` টায় অটো-লাইক চলে যাবে।", parse_mode='Markdown')
    else:
        await update.message.reply_text(f"❌ UID: `{uid}`-এর জন্য কোনো সক্রিয় প্যাকেজ খুঁজে পাওয়া যায়নি। প্রথমে `/add` দিয়ে প্যাকেজ কিনুন।", parse_mode='Markdown')
    
    conn.close()

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

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "(👍 ‿ 👍)✍️ **Like Prices**\n"
        "_______________________\n\n"
        "👉 Instant Like: /like `<UID>` ⇨ 8.0 BDT / 100 Likes\n"
        "👉 Daily Package: /add `<UID>` `30D` ⇨ 8.0 BDT / Day\n"
        "👉 Set Daily Time: /time `<UID>` `HH:MM` (e.g. `/time 12345 21:30`)\n"
        "_______________________\n\n"
        "💎 **Diamond Prices**\n"
        "• 115 Diamond - 80 BDT\n"
        "• 240 Diamond - 160 BDT"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    await update.message.reply_text(f"💰 আপনার বর্তমান ওয়ালেট ব্যালেন্স: {bal} BDT")

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

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT uid, days, start_date, end_date, preferred_time FROM subscriptions WHERE user_id = ? ORDER BY id DESC', (user_id,))
    subs = cursor.fetchall()
    conn.close()

    if not subs:
        await update.message.reply_text("❌ আপনার কোনো সক্রিয় লাইক প্যাকেজ পাওয়া যায়নি।")
        return

    msg = "📊 **আপনার লাইক প্যাকেজ ব্যবহারের বিবরণ:**\n\n"
    now = datetime.now()

    for sub in subs:
        uid, days, start_str, end_str, pref_time = sub
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
            f"⏰ ডেইলি টাইম: `{pref_time}`\n"
            f"⏱️ ব্যবহৃত হয়েছে: {used_days} দিন\n"
            f"⏳ বাকি আছে: {remaining_days} দিন\n"
            f"_______________________\n"
        )

    await update.message.reply_text(msg, parse_mode='Markdown')

# --- ADMIN PANEL COMMANDS ---
async def admin_add_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ ব্যবহারবিধি: `/addbalance <User_ID> <পরিমাণ>`", parse_mode='Markdown')
        return

    try:
        target_user = int(context.args[0])
        amount = float(context.args[1])
        add_balance(target_user, amount)
        new_bal = get_balance(target_user)
        
        await update.message.reply_text(f"✅ User ID: `{target_user}` -এর ওয়ালেটে {amount} BDT যোগ করা হয়েছে।\nবর্তমান ব্যালেন্স: {new_bal} BDT", parse_mode='Markdown')
        
        try:
            await context.bot.send_message(
                chat_id=target_user,
                text=f"🎉 **ব্যালেন্স আপডেট!**\n\nআপনার ওয়ালেটে {amount} BDT যোগ করা হয়েছে।\nবর্তমান ওয়ালেট ব্যালেন্স: {new_bal} BDT",
                parse_mode='Markdown'
            )
        except Exception:
            pass
    except ValueError:
        await update.message.reply_text("❌ সঠিক সংখ্যা লিখুন।")

async def admin_cut_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if len(context.args) < 2:
        await update.message.reply_text("❌ ব্যবহারবিধি: `/cutbalance <User_ID> <পরিমাণ>`", parse_mode='Markdown')
        return

    try:
        target_user = int(context.args[0])
        amount = float(context.args[1])
        add_balance(target_user, -amount)
        new_bal = get_balance(target_user)
        
        await update.message.reply_text(f"✅ User ID: `{target_user}` -এর অ্যাকাউন্ট থেকে {amount} BDT কাটা হয়েছে।\nবর্তমান ব্যালেন্স: {new_bal} BDT", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ সঠিক সংখ্যা লিখুন।")

async def admin_check_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("❌ ব্যবহারবিধি: `/checkuser <User_ID>`", parse_mode='Markdown')
        return

    try:
        target_user = int(context.args[0])
        bal = get_balance(target_user)
        await update.message.reply_text(f"👤 **ইউজার তথ্য:**\n\n🆔 User ID: `{target_user}`\n💰 ব্যালেন্স: {bal} BDT", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("❌ সঠিক ID প্রদান করুন।")

async def admin_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    if not context.args:
        await update.message.reply_text("❌ ব্যবহারবিধি: `/broadcast <আপনার বার্তা>`", parse_mode='Markdown')
        return

    msg_text = " ".join(context.args)
    conn = sqlite3.connect('bot_database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users')
    users = cursor.fetchall()
    conn.close()

    success, failed = 0, 0
    await update.message.reply_text("⏳ মেসেজ পাঠানো শুরু হচ্ছে...")

    for u in users:
        try:
            await context.bot.send_message(chat_id=u[0], text=f"📢 **নোটিশ:**\n\n{msg_text}", parse_mode='Markdown')
            success += 1
        except Exception:
            failed += 1

    await update.message.reply_text(f"✅ ব্রডকাস্ট সম্পন্ন!\n\nসফল: {success} জন\nব্যর্থ: {failed} জন")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    if query.data in ['ff_like', 'ff_diamond']:
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

# --- Main Async Runner for Render ---
async def main():
    init_db()
    TOKEN = "8915748936:AAEJw_iwXbnuMQzrEIAJF163iRPe-30rlpY"
    
    application = Application.builder().token(TOKEN).build()

    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHa
