
import os
import sqlite3
import asyncio
import threading
import secrets
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
DEFAULT_LIKE_API_KEY = os.environ.get("LIKE_API_KEY", "").strip()
DB_PATH = os.environ.get("DB_PATH", "bot.db")
PORT = int(os.environ.get("PORT", "10000"))
BD_TZ = ZoneInfo("Asia/Dhaka")

ADMIN_IDS = {6347427263, 6992868111}
TELEGRAM_SUPPORT_USERNAME = os.environ.get("SUPPORT_USERNAME", "@maruf3900")
WHATSAPP_NUMBER = os.environ.get("WHATSAPP_NUMBER", "+8801618203922")
REDEEM_LINK = os.environ.get("REDEEM_LINK", "https://shop.garena.my")

DEFAULT_PRICES = {
    "d25": 20.0, "d50": 35.0, "d115": 80.0, "d240": 160.0,
    "d610": 400.0, "weekly": 160.0, "monthly": 800.0,
    "like_7days": 50.0, "like_30days": 180.0,
}
PKGS = ("25", "50", "115", "240", "610", "weekly", "monthly")

app = Flask(__name__)
checker_task = None


@app.route("/")
def home():
    return "Bot is Live 24/7!"


def now_bd():
    return datetime.now(BD_TZ)


def db():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        balance REAL NOT NULL DEFAULT 0,
        api_key TEXT,
        created_at TEXT NOT NULL)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS subscriptions(
        id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        uid TEXT NOT NULL,
        daily_likes INTEGER NOT NULL,
        start_date TEXT NOT NULL,
        end_date TEXT NOT NULL,
        auto_time TEXT NOT NULL DEFAULT '12:00',
        last_sent_date TEXT,
        active INTEGER NOT NULL DEFAULT 1)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS vouchers(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        package TEXT NOT NULL,
        code TEXT NOT NULL UNIQUE,
        used INTEGER NOT NULL DEFAULT 0,
        used_by INTEGER,
        used_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS transactions(
        trx_id TEXT PRIMARY KEY,
        user_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        approved_at TEXT,
        approved_by INTEGER)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS prices(
        item TEXT PRIMARY KEY,
        price REAL NOT NULL)""")

    for item, price in DEFAULT_PRICES.items():
        cur.execute(
            "INSERT OR IGNORE INTO prices(item,price) VALUES(?,?)",
            (item, price)
        )

    conn.commit()
    conn.close()


def ensure_user(user_id):
    conn = db()
    conn.execute(
        "INSERT OR IGNORE INTO users(user_id,created_at) VALUES(?,?)",
        (user_id, now_bd().isoformat())
    )
    conn.commit()
    conn.close()


def get_balance(user_id):
    conn = db()
    row = conn.execute(
        "SELECT balance FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()
    return float(row["balance"]) if row else 0.0


def get_api_key(user_id):
    conn = db()
    row = conn.execute(
        "SELECT api_key FROM users WHERE user_id=?",
        (user_id,)
    ).fetchone()
    conn.close()

    if row and row["api_key"]:
        return row["api_key"]

    return DEFAULT_LIKE_API_KEY


def set_api_key(user_id, key):
    conn = db()
    conn.execute(
        "UPDATE users SET api_key=? WHERE user_id=?",
        (key, user_id)
    )
    conn.commit()
    conn.close()


def get_price(item):
    conn = db()
    row = conn.execute(
        "SELECT price FROM prices WHERE item=?",
        (item,)
    ).fetchone()
    conn.close()
    return float(row["price"]) if row else 0.0


def set_price(item, price):
    conn = db()
    conn.execute(
        "INSERT OR REPLACE INTO prices(item,price) VALUES(?,?)",
        (item, price)
    )
    conn.commit()
    conn.close()


def add_balance(user_id, amount):
    conn = db()
    conn.execute(
        "UPDATE users SET balance=balance+? WHERE user_id=?",
        (amount, user_id)
    )
    conn.commit()
    conn.close()


def is_admin(user_id):
    return user_id in ADMIN_IDS


def fmt_money(value):
    return f"{value:.2f}".rstrip("0").rstrip(".")


def send_like_request(api_key, uid):
    import requests

    if not api_key:
        return None, 0

    endpoints = [
        "https://key.like.mlbbshop.com/like",
        "https://freefirelike.com/api/like",
        "https://buykey.freefirelike.com/like",
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    for endpoint in endpoints:
        try:
            response = requests.get(
                endpoint,
                params={"key": api_key, "uid": uid},
                headers=headers,
                timeout=10
            )

            try:
                data = response.json()
            except Exception:
                data = None

            if response.status_code == 200 and isinstance(data, dict):
                return data, 200

        except requests.RequestException:
            continue

    return None, 0


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    keyboard = [
        [
            InlineKeyboardButton("🔥 Free Fire Like", callback_data="ff_like"),
            InlineKeyboardButton("💎 Free Fire Diamond", callback_data="ff_diamond")
        ],
        [
            InlineKeyboardButton("💳 My Balance", callback_data="my_balance"),
            InlineKeyboardButton("📦 Stock Check", callback_data="check_stock")
        ],
        [
            InlineKeyboardButton("📞 Support", callback_data="support")
        ]
    ]

    await update.message.reply_text(
        "👋 স্বাগতম মারুফ লাইক ও টপ-আপ বটে!\n\n"
        "সকল কমান্ড দেখতে /help ব্যবহার করুন।",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📜 <b>সকল কমান্ড</b>\n\n"
        "/key [KEY] — API Key সেট\n"
        "/help — Help\n"
        "/support — Support\n"
        "/number — Payment number\n"
        "/rate — Price list\n"
        "/balance — Wallet balance\n"
        "/stock — Voucher stock\n"
        "/tp [UID] [Package] — Voucher purchase\n"
        "/verify [TrxID] [Amount] — Deposit request\n"
        "/add [UID] [Likes] [Days] — Auto-like schedule\n"
        "/delete [Schedule_ID] — Schedule delete\n"
        "/list — Active schedules\n"
        "/time [Schedule_ID] [HH:MM] — Schedule time\n"
        "/like [UID] — Instant like\n"
        "/usage — API status\n\n"
        "<b>Admin</b>\n"
        "/addvoucher [Package] [Code]\n"
        "/setrate [Type] [Package] [Price]\n"
        "/approve [TrxID]\n"
        "/reject [TrxID]\n"
        "/addbalance [UserID] [Amount]\n"
        "/admin"
    )

    await update.message.reply_text(text, parse_mode="HTML")


async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📞 Customer Support\n"
        f"Telegram: {TELEGRAM_SUPPORT_USERNAME}\n"
        f"WhatsApp: {WHATSAPP_NUMBER}"
    )


async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💳 Payment Number\n"
        "bKash/Nagad Personal: 01618203922\n\n"
        "পেমেন্ট করার পর /verify TrxID Amount ব্যবহার করুন।"
    )


async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    labels = [
        ("d25", "25 Diamonds"),
        ("d50", "50 Diamonds"),
        ("d115", "115 Diamonds"),
        ("d240", "240 Diamonds"),
        ("d610", "610 Diamonds"),
        ("weekly", "Weekly Membership"),
        ("monthly", "Monthly Membership"),
        ("like_7days", "100 Likes/Day — 7 Days"),
        ("like_30days", "100 Likes/Day — 30 Days"),
    ]

    text = "💰 <b>Current Price List</b>\n\n"

    for key, label in labels:
        text += f"• {label}: ৳{fmt_money(get_price(key))}\n"

    await update.message.reply_text(text, parse_mode="HTML")


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    await update.message.reply_text(
        f"💳 আপনার ব্যালেন্স: ৳{fmt_money(get_balance(user_id))}"
    )


async def key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    if not context.args:
        current = get_api_key(user_id)

        if current and len(current) > 4:
            masked = current[:4] + "••••••••"
        else:
            masked = "Not set"

        await update.message.reply_text(
            f"🔑 বর্তমান API Key: {masked}\n"
            "নতুন Key সেট করতে: /key YOUR_API_KEY"
        )
        return

    new_key = context.args[0].strip()

    if len(new_key) < 4 or len(new_key) > 200:
        await update.message.reply_text("❌ API Key-এর format সঠিক নয়।")
        return

    set_api_key(user_id, new_key)

    await update.message.reply_text(
        "✅ আপনার API Key নিরাপদভাবে সংরক্ষণ করা হয়েছে।"
    )


async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ ব্যবহার:\n/verify [TrxID] [Amount]\n\n"
            "উদাহরণ:\n/verify 9X82K10L 500"
        )
        return

    trx_id = context.args[0].strip().upper()

    try:
        amount = float(context.args[1])

        if amount <= 0:
            raise ValueError

    except ValueError:
        await update.message.reply_text("❌ Amount সঠিকভাবে দিন।")
        return

    conn = db()

    existing = conn.execute(
        "SELECT status FROM transactions WHERE trx_id=?",
        (trx_id,)
    ).fetchone()

    if existing:
        conn.close()

        await update.message.reply_text(
            f"⚠️ এই TrxID ইতোমধ্যে {existing['status']} অবস্থায় আছে।"
        )
        return

    conn.execute(
        """
        INSERT INTO transactions
        (trx_id,user_id,amount,status,created_at)
        VALUES(?,?,?,?,?)
        """,
        (
            trx_id,
            user_id,
            amount,
            "pending",
            now_bd().isoformat()
        )
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"⏳ TrxID {trx_id} জমা হয়েছে।\n"
        f"Amount: ৳{fmt_money(amount)}\n\n"
        "Admin payment যাচাই করে approve করলে balance যোগ হবে।"
    )

    for admin in ADMIN_IDS:
        try:
            await context.bot.send_message(
                admin,
                f"💰 নতুন Deposit Request\n\n"
                f"User: {user_id}\n"
                f"TrxID: {trx_id}\n"
                f"Amount: ৳{fmt_money(amount)}\n\n"
                f"Approve: /approve {trx_id}\n"
                f"Reject: /reject {trx_id}"
            )
        except Exception:
            pass


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    if len(context.args) != 3:
        await update.message.reply_text(
            "❌ /add [UID] [Likes] [Days]"
        )
        return

    player_uid = context.args[0].strip()

    try:
        likes = int(context.args[1])
        days = int(context.args[2])

        if likes <= 0 or days <= 0 or days > 365:
            raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ Likes/Days সঠিক সংখ্যা দিন। Days সর্বোচ্চ 365।"
        )
        return

    schedule_id = secrets.token_hex(4).upper()
    start = now_bd()
    end = start + timedelta(days=days)

    conn = db()

    conn.execute(
        """
        INSERT INTO subscriptions
        (id,user_id,uid,daily_likes,start_date,end_date,auto_time)
        VALUES(?,?,?,?,?,?,?)
        """,
        (
            schedule_id,
            user_id,
            player_uid,
            likes,
            start.isoformat(),
            end.isoformat(),
            "12:00"
        )
    )

    conn.commit()
    conn.close()

    await update.message.reply_text(
        f"✅ Schedule তৈরি হয়েছে!\n\n"
        f"UID: {player_uid}\n"
        f"Daily Likes: {likes}\n"
        f"Days: {days}\n"
        f"Schedule ID: {schedule_id}\n"
        f"Default Time: 12:00"
    )


async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    conn = db()

    rows = conn.execute(
        """
        SELECT * FROM subscriptions
        WHERE user_id=? AND active=1
        ORDER BY start_date
        """,
        (user_id,)
    ).fetchall()

    conn.close()

    if not rows:
        await update.message.reply_text(
            "📋 কোনো active schedule নেই।"
        )
        return

    text = "📋 <b>Active Schedules</b>\n\n"

    for row in rows:
        text += (
            f"🆔 <code>{row['id']}</code>\n"
            f"🎯 UID: <code>{row['uid']}</code>\n"
            f"❤️ Daily: {row['daily_likes']}\n"
            f"⏰ Time: {row['auto_time']}\n"
            f"📅 End: {row['end_date'][:10]}\n\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ /time [Schedule_ID] [HH:MM]\n\n"
            "উদাহরণ:\n/time A1B2C3D4 18:27"
        )
        return

    schedule_id = context.args[0].upper()
    time_input = context.args[1]

    try:
        parsed_time = datetime.strptime(
            time_input,
            "%H:%M"
        ).strftime("%H:%M")

    except ValueError:
        await update.message.reply_text(
            "❌ সময় HH:MM format-এ দিন।"
        )
        return

    conn = db()

    cur = conn.execute(
        """
        UPDATE subscriptions
        SET auto_time=?
        WHERE id=? AND user_id=? AND active=1
        """,
        (
            parsed_time,
            schedule_id,
            user_id
        )
    )

    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed:
        await update.message.reply_text(
            f"✅ Schedule {schedule_id}-এর সময় {parsed_time} করা হয়েছে।"
        )
    else:
        await update.message.reply_text(
            "❌ Schedule ID পাওয়া যায়নি।"
        )


async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ /delete [Schedule_ID]"
        )
        return

    schedule_id = context.args[0].upper()

    conn = db()

    cur = conn.execute(
        """
        UPDATE subscriptions
        SET active=0
        WHERE id=? AND user_id=? AND active=1
        """,
        (
            schedule_id,
            user_id
        )
    )

    conn.commit()
    changed = cur.rowcount
    conn.close()

    if changed:
        await update.message.reply_text(
            "🗑️ Schedule সফলভাবে delete হয়েছে।"
        )
    else:
        await update.message.reply_text(
            "❌ Schedule ID পাওয়া যায়নি।"
        )


async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if len(context.args) != 1:
        await update.message.reply_text(
            "❌ /like [UID]"
        )
        return

    player_uid = context.args[0].strip()
    api_key = get_api_key(user_id)

    if not api_key:
        await update.message.reply_text(
            "❌ Like API Key সেট করা নেই। /key ব্যবহার করুন।"
        )
        return

    await update.message.reply_text(
        "⏳ Like request পাঠানো হচ্ছে..."
    )

    data, status = await asyncio.to_thread(
        send_like_request,
        api_key,
        player_uid
    )

    if status == 200 and data:
        name = (
            data.get("Name")
            or data.get("player_name")
            or "N/A"
        )

        sent = (
            data.get("Likes Sent")
            or data.get("likes_sent")
            or "N/A"
        )

        before = (
            data.get("Before")
            or data.get("before")
            or "N/A"
        )

        after = (
            data.get("After")
            or data.get("after")
            or "N/A"
        )

        remaining = (
            data.get("Daily Remaining")
            or data.get("daily_remaining")
            or "N/A"
        )

        await update.message.reply_text(
            f"🔥 <b>MARUF LIKE BOT</b>\n\n"
            f"✅ Likes request সফল\n"
            f"👤 UID: <code>{player_uid}</code>\n"
            f"📛 Name: {name}\n"
            f"❤️ Likes: +{sent}\n"
            f"📊 Before: {before}\n"
            f"📈 After: {after}\n"
            f"⚡ Remaining: {remaining}\n"
            f"🕒 {now_bd().strftime('%I:%M %p, %d %b %Y')}",
            parse_mode="HTML"
        )

    else:
        await update.message.reply_text(
            "❌ Like provider থেকে request সফল হয়নি।\n"
            "API Key, UID অথবা provider status পরীক্ষা করুন।"
        )


async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    api_key = get_api_key(user_id)

    if not api_key:
        await update.message.reply_text(
            "❌ API Key সেট করা নেই।"
        )
        return

    data, status = await asyncio.to_thread(
        send_like_request,
        api_key,
        "100000000"
    )

    remaining = "N/A"

    if isinstance(data, dict):
        remaining = (
            data.get("Daily Remaining")
            or data.get("daily_remaining")
            or "N/A"
        )

    await update.message.reply_text(
        f"🔑 API Status: {'🟢 Active' if status == 200 else '🔴 Error'}\n"
        f"⚡ Daily Remaining: {remaining}"
    )


async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = db()

    text = "📦 <b>Voucher Stock</b>\n\n"

    for package in PKGS:
        row = conn.execute(
            """
            SELECT COUNT(*) AS c
            FROM vouchers
            WHERE package=? AND used=0
            """,
            (package,)
        ).fetchone()

        text += f"• {package.upper()}: {row['c']} Pcs\n"

    conn.close()

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


async def topup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ensure_user(user_id)

    if len(context.args) != 2:
        await update.message.reply_text(
            "❌ /tp [Player_UID] [Package]"
        )
        return

    player_uid = context.args[0].strip()
    package = context.args[1].lower().strip()

    if package not in PKGS:
        await update.message.reply_text(
            "❌ Package:\n25, 50, 115, 240, 610, weekly, monthly"
        )
        return

    price_key = f"d{package}" if package.isdigit() else package
    price = get_price(price_key)

    conn = db()

    try:
        conn.execute("BEGIN IMMEDIATE")

        user = conn.execute(
            "SELECT balance FROM users WHERE user_id=?",
            (user_id,)
        ).fetchone()

        if not user or float(user["balance"]) < price:
            conn.rollback()
            await update.message.reply_text(
                f"❌ পর্যাপ্ত balance নেই।\n"
                f"প্রয়োজন: ৳{fmt_money(price)}\n"
                f"আপনার balance: ৳{fmt_money(float(user['balance']) if user else 0)}"
            )
            return

        voucher = conn.execute(
            """
  
