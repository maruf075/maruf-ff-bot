import os
import sqlite3
import asyncio
import threading
import logging
import requests
from datetime import datetime
from flask import Flask
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# =========================================================
# CONFIG
# =========================================================

BOT_TOKEN = os.getenv("8915748936:AAFtZ08QQ-_BBvrwjMydusssz9A5e1ME6i0", "").strip()

ADMIN_IDS = {
    6347427263,
    6992868111,
}

TELEGRAM_SUPPORT = "@maruf3900"
WHATSAPP_NUMBER = "01618203922"

DB_PATH = os.getenv("DB_PATH", "bot.db")

# ---------------------------------------------------------
# Payment numbers
# ---------------------------------------------------------

DEFAULT_BKASH = "01618203922"
DEFAULT_NAGAD = "01842408034"

# ---------------------------------------------------------
# Like API
# ---------------------------------------------------------

LIKE_API_URL = os.getenv(
    "LIKE_API_URL",
    "https://api.freefirelike.com/like"
).strip()

LIKE_API_KEY = os.getenv("VALT2H", "").strip()

# ---------------------------------------------------------
# Profile API
# ---------------------------------------------------------

PROFILE_API_URL = os.getenv("PROFILE_API_URL", "").strip()
PROFILE_API_KEY = os.getenv("PROFILE_API_KEY", "").strip()

# ---------------------------------------------------------
# Topup API
# ---------------------------------------------------------

TOPUP_API_URL = os.getenv("TOPUP_API_URL", "").strip()
TOPUP_API_KEY = os.getenv("TOPUP_API_KEY", "").strip()


# =========================================================
# LOGGING
# =========================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


# =========================================================
# FLASK SERVER FOR RENDER
# =========================================================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "MARUF FF BOT is running."


@web_app.route("/health")
def health():
    return {
        "status": "ok",
        "service": "maruf-ff-bot"
    }


def run_web():
    port = int(os.getenv("PORT", "10000"))

    web_app.run(
        host="0.0.0.0",
        port=port,
        debug=False,
        use_reloader=False
    )


# =========================================================
# DATABASE
# =========================================================

def get_db():
    conn = sqlite3.connect(
        DB_PATH,
        check_same_thread=False
    )
    conn.row_factory = sqlite3.Row
    return conn


def init_db():

    conn = get_db()
    cur = conn.cursor()

    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL DEFAULT 0,
            due REAL DEFAULT 0,
            advance REAL DEFAULT 0,
            total_payment REAL DEFAULT 0,
            total_spent REAL DEFAULT 0,
            created_at TEXT
        )
    """)

    # Settings
    cur.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)

    # Orders
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            uid TEXT,
            package TEXT,
            price REAL DEFAULT 0,
            status TEXT DEFAULT 'Pending',
            trxid TEXT,
            created_at TEXT
        )
    """)

    # Payment requests
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            method TEXT,
            amount REAL,
            trxid TEXT,
            screenshot TEXT,
            status TEXT DEFAULT 'Pending',
            created_at TEXT
        )
    """)

    # Default settings
    defaults = {
        "bkash": DEFAULT_BKASH,
        "nagad": DEFAULT_NAGAD,
    }

    for key, value in defaults.items():

        cur.execute(
            "SELECT value FROM settings WHERE key=?",
            (key,)
        )

        if cur.fetchone() is None:

            cur.execute(
                "INSERT INTO settings(key,value) VALUES(?,?)",
                (key, value)
            )

    conn.commit()
    conn.close()


def setting(key, default=""):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT value FROM settings WHERE key=?",
        (key,)
    )

    row = cur.fetchone()

    conn.close()

    if row:
        return row["value"]

    return default


def set_setting(key, value):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO settings(key,value)
        VALUES(?,?)
        ON CONFLICT(key)
        DO UPDATE SET value=excluded.value
    """, (key, str(value)))

    conn.commit()
    conn.close()


# =========================================================
# USER DATABASE
# =========================================================

def save_user(user):

    if not user:
        return

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT id FROM users WHERE id=?",
        (user.id,)
    )

    exists = cur.fetchone()

    username = user.username or ""
    first_name = user.first_name or ""

    if exists:

        cur.execute("""
            UPDATE users
            SET username=?, first_name=?
            WHERE id=?
        """, (
            username,
            first_name,
            user.id
        ))

    else:

        cur.execute("""
            INSERT INTO users(
                id,
                username,
                first_name,
                created_at
            )
            VALUES(?,?,?,?,?)
        """, (
            user.id,
            username,
            first_name,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))

    conn.commit()
    conn.close()


def get_user(user_id):

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE id=?",
        (user_id,)
    )

    row = cur.fetchone()

    conn.close()

    return row


def change_balance(user_id, amount):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET balance = balance + ?
        WHERE id=?
    """, (
        amount,
        user_id
    ))

    conn.commit()
    conn.close()


def set_balance(user_id, amount):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET balance=?
        WHERE id=?
    """, (
        amount,
        user_id
    ))

    conn.commit()
    conn.close()


def set_due(user_id, amount):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET due=?
        WHERE id=?
    """, (
        amount,
        user_id
    ))

    conn.commit()
    conn.close()


def set_advance(user_id, amount):

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE users
        SET advance=?
        WHERE id=?
    """, (
        amount,
        user_id
    ))

    conn.commit()
    conn.close()


# =========================================================
# HELPERS
# =========================================================

def is_admin(user_id):

    return user_id in ADMIN_IDS


def money(value):

    try:
        value = float(value)

        if value.is_integer():
            return str(int(value))

        return f"{value:.2f}"

    except Exception:
        return "0"


def user_text(row):

    if not row:
        return "User not found."

    return (
        f"👤 <b>Account</b>\n\n"
        f"🆔 ID: <code>{row['id']}</code>\n"
        f"👤 Name: {row['first_name'] or '-'}\n"
        f"🔹 Username: @{row['username'] if row['username'] else '-'}\n\n"
        f"💰 Balance: ৳{money(row['balance'])}\n"
        f"📌 Due: ৳{money(row['due'])}\n"
        f"➕ Advance: ৳{money(row['advance'])}\n"
        f"💳 Total Payment: ৳{money(row['total_payment'])}\n"
        f"🛒 Total Spent: ৳{money(row['total_spent'])}"
    )


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user

    save_user(user)

    keyboard = [
        [
            InlineKeyboardButton(
                "💰 Balance",
                callback_data="balance"
            ),
            InlineKeyboardButton(
                "💳 Add Balance",
                callback_data="add_balance"
            ),
        ],
        [
            InlineKeyboardButton(
                "❤️ Free Fire Like",
                callback_data="like_help"
            ),
            InlineKeyboardButton(
                "🔎 UID Info",
                callback_data="uid_help"
            ),
        ],
        [
            InlineKeyboardButton(
                "💎 Top Up",
                callback_data="topup_help"
            ),
        ],
        [
            InlineKeyboardButton(
                "📞 Support",
                callback_data="support"
            ),
        ],
    ]

    if is_admin(user.id):

        keyboard.append([
            InlineKeyboardButton(
                "⚙️ Admin Panel",
                callback_data="admin"
            )
        ])

    text = (
        "🔥 <b>MARUF FF BOT</b>\n\n"
        "স্বাগতম! নিচের মেনু থেকে সার্ভিস নির্বাচন করুন।\n\n"
        "💎 Free Fire Services\n"
        "❤️ Like Service\n"
        "🔎 UID Information\n"
        "💰 Balance System\n"
        "💳 Payment System\n"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# =========================================================
# HELP
# =========================================================

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    text = (
        "📚 <b>MARUF FF BOT HELP</b>\n\n"
        "/start - Main Menu\n"
        "/balance - Balance দেখুন\n"
        "/number - Payment Number\n"
        "/like UID - Free Fire Like\n"
        "/uid UID - Player Information\n"
        "/add - Balance Add করার নিয়ম\n"
        "/support - Support\n"
    )

    if is_admin(update.effective_user.id):

        text += (
            "\n<b>Admin Commands</b>\n\n"
            "/admin - Admin Panel\n"
            "/users - সব User\n"
            "/addbalance USER_ID AMOUNT\n"
            "/cutbalance USER_ID AMOUNT\n"
            "/setbalance USER_ID AMOUNT\n"
            "/setdue USER_ID AMOUNT\n"
            "/setadvance USER_ID AMOUNT\n"
            "/setbkash NUMBER\n"
            "/setnagad NUMBER\n"
        )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# BALANCE
# =========================================================

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    row = get_user(update.effective_user.id)

    await update.message.reply_text(
        user_text(row),
        parse_mode="HTML"
    )


# =========================================================
# PAYMENT NUMBER
# =========================================================

async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    bkash = setting("bkash", DEFAULT_BKASH)
    nagad = setting("nagad", DEFAULT_NAGAD)

    text = (
        "💳 <b>Payment Numbers</b>\n\n"
        f"🟣 bKash: <code>{bkash}</code>\n"
        f"🟠 Nagad: <code>{nagad}</code>\n\n"
        "পেমেন্ট করার পর Transaction ID দিয়ে Verify Request দিন।"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# ADD BALANCE
# =========================================================

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    bkash = setting("bkash", DEFAULT_BKASH)
    nagad = setting("nagad", DEFAULT_NAGAD)

    text = (
        "💰 <b>Balance Add</b>\n\n"
        f"🟣 bKash: <code>{bkash}</code>\n"
        f"🟠 Nagad: <code>{nagad}</code>\n\n"
        "পেমেন্ট করার পর নিচের তথ্য পাঠান:\n\n"
        "<code>/verify AMOUNT TRXID</code>\n\n"
        "উদাহরণ:\n"
        "<code>/verify 100 ABC123XYZ</code>\n\n"
        "⚠️ বর্তমানে Verification Admin approval ভিত্তিক।"
    )

    await update.message.reply_text(
        text,
        parse_mode="HTML"
    )


# =========================================================
# VERIFY REQUEST
# =========================================================

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    if len(context.args) < 2:

        await update.message.reply_text(
            "ব্যবহার করুন:\n"
            "<code>/verify AMOUNT TRXID</code>",
            parse_mode="HTML"
        )

        return

    try:
        amount = float(context.args[0])
    except Exception:

        await update.message.reply_text(
            "❌ Amount সঠিক নয়।"
        )

        return

    trxid = context.args[1]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO payments(
            telegram_id,
            amount,
            trxid,
            status,
            created_at
        )
        VALUES(?,?,?,?,?)
    """, (
        update.effective_user.id,
        amount,
        trxid,
        "Pending",
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    await update.message.reply_text(
        "✅ আপনার Payment Verification Request গ্রহণ করা হয়েছে।\n\n"
        f"💰 Amount: ৳{money(amount)}\n"
        f"🧾 TRXID: <code>{trxid}</code>\n"
        "⏳ Status: Pending",
        parse_mode="HTML"
    )

    for admin_id in ADMIN_IDS:

        try:

            await context.bot.send_message(
                admin_id,
                "💳 <b>New Payment Request</b>\n\n"
                f"👤 User ID: <code>{update.effective_user.id}</code>\n"
                f"💰 Amount: ৳{money(amount)}\n"
                f"🧾 TRXID: <code>{trxid}</code>",
                parse_mode="HTML"
            )

        except Exception as e:

            logger.error(e)


# =========================================================
# SUPPORT
# =========================================================

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    await update.message.reply_text(
        "📞 <b>Support</b>\n\n"
        f"Telegram: {TELEGRAM_SUPPORT}\n"
        f"WhatsApp: <code>{WHATSAPP_NUMBER}</code>",
        parse_mode="HTML"
    )


# =========================================================
# LIKE API
# =========================================================

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    if not context.args:

        await update.message.reply_text(
            "ব্যবহার:\n"
            "<code>/like UID</code>",
            parse_mode="HTML"
        )

        return

    uid = context.args[0]

    if not LIKE_API_KEY:

        await update.message.reply_text(
            "❌ Like API Key সেট করা হয়নি।\n\n"
            "Admin/Render Environment Variables থেকে "
            "LIKE_API_KEY সেট করুন।"
        )

        return

    await update.message.reply_text(
        "⏳ Like request processing..."
    )

    try:

        params = {
            "key": LIKE_API_KEY,
            "uid": uid,
        }

        response = requests.get(
            LIKE_API_URL,
            params=params,
            timeout=20
        )

        if response.status_code != 200:

            await update.message.reply_text(
                f"❌ API Error: {response.status_code}"
            )

            return

        try:

            data = response.json()

        except Exception:

            data = {}

        name = (
            data.get("Name")
            or data.get("name")
            or data.get("player_name")
            or data.get("Player Nickname")
            or "Unknown"
        )

        likes = (
            data.get("Likes Sent")
            or data.get("likes_sent")
            or data.get("LikesGiven")
            or data.get("likes")
            or data.get("likes_given")
            or "N/A"
        )

        await update.message.reply_text(
            "❤️ <b>LIKE RESULT</b>\n\n"
            f"🆔 UID: <code>{uid}</code>\n"
            f"👤 Name: <b>{name}</b>\n"
            f"❤️ Likes Sent: <b>{likes}</b>\n\n"
            "✅ Request completed.",
            parse_mode="HTML"
        )

    except Exception as e:

        logger.error(e)

        await update.message.reply_text(
            "❌ Like API থেকে response পাওয়া যায়নি।"
        )


# =========================================================
# PROFILE / UID API
# =========================================================

async def uid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    save_user(update.effective_user)

    if not context.args:

        await update.message.reply_text(
            "ব্যবহার:\n"
            "<code>/uid UID</code>",
            parse_mode="HTML"
        )

        return

    uid = context.args[0]

    if not PROFILE_API_URL:

        await update.message.reply_text(
            "❌ Profile API এখনো configure করা হয়নি।\n\n"
            "Render Environment Variables-এ:\n"
            "PROFILE_API_URL\n"
            "PROFILE_API_KEY\n"
            "সেট করতে হবে।"
        )

        return

    await update.message.reply_text(
        "🔎 Player information খোঁজা হচ্ছে..."
    )

    try:

        headers = {}

        if PROFILE_API_KEY:

            headers["x-api-key"] = PROFILE_API_KEY
            headers["Authorization"] = f"Bearer {PROFILE_API_KEY}"

        params = {
            "uid": uid,
            "region": "BD",
        }

        response = requests.get(
            PROFILE_API_URL,
            params=params,
            headers=headers,
            timeout=20
        )

        if response.status_code != 200:

            await update.message.reply_text(
                f"❌ Profile API Error: {response.status_code}"
            )

            return

        data = response.json()

        # Common API formats
        if isinstance(data, dict):

            basic = (
                data.get("basicInfo")
                or data.get("basic_info")
                or data.get("data")
                or data
            )

        else:

            basic = {}

        def get_value(*keys):

            for key in keys:

                if key in basic and basic[key] not in (
                    None,
                    "",
                    []
                ):

                    return basic[key]

            return "N/A"

        name = get_value(
            "AccountName",
            "nickname",
            "NickName",
            "name",
            "player_name"
        )

        level = get_value(
            "AccountLevel",
            "level",
            "Level"
        )

        region = get_value(
            "AccountRegion",
            "region",
            "Region"
        )

        likes = get_value(
            "AccountLikes",
            "liked",
            "likes",
            "Likes"
        )

        br_rank = get_value(
            "BrMaxRank",
            "rank",
            "BRRan
