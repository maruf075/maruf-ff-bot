import os
import re
import json
import sqlite3
import asyncio
import threading
from datetime import datetime, timedelta, timezone
from threading import Thread

import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.constants import ParseMode
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes,
)

# ============================================================
# CONFIG
# ============================================================
# Bot token intentionally left blank. Put it in Render Environment Variables.
BOT_TOKEN = os.getenv("BOT_TOKEN", "")

# The Like API key shown in the user's uploaded dashboard screenshot.
# Change/rotate it later if the provider issues a new key.
LIKE_API_KEY = os.getenv("LIKE_API_KEY", "VALT2H")
LIKE_API_URL = os.getenv("LIKE_API_URL", "https://api.freefirelike.com/like")

ADMIN_IDS = {6347427263, 6992868111}
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"
WHATSAPP_NUMBER = "01618203922"
DEFAULT_BKASH = "01618203922"
DEFAULT_NAGAD = "01842408034"
DB_PATH = os.getenv("DB_PATH", "bot.db")

DEFAULT_PRICES = {
    "d25": 20.0,
    "d50": 35.0,
    "d115": 80.0,
    "d240": 160.0,
    "d610": 400.0,
    "weekly": 160.0,
    "monthly": 800.0,
    "like_7days": 50.0,
    "like_30days": 180.0,
}

web_app = Flask(__name__)

@web_app.route("/")
def home():
    return "MARUF FF BOT is running."

@web_app.route("/health")
def health():
    return {"status": "ok", "service": "maruf-ff-bot"}

def run_flask():
    port = int(os.environ.get("PORT", "8080"))
    web_app.run(host="0.0.0.0", port=port, use_reloader=False)

# ============================================================
# DATABASE
# ============================================================
_db_lock = threading.Lock()

def db():
    conn = sqlite3.connect(DB_PATH, timeout=30, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with _db_lock:
        con = db()
        cur = con.cursor()
        cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance REAL NOT NULL DEFAULT 0,
            due REAL NOT NULL DEFAULT 0,
            advance REAL NOT NULL DEFAULT 0,
            blocked INTEGER NOT NULL DEFAULT 0,
            total_spent REAL NOT NULL DEFAULT 0,
            total_added REAL NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            last_seen TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            sub_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            uid TEXT NOT NULL,
            daily_likes INTEGER NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            auto_time TEXT NOT NULL DEFAULT '12:00',
            active INTEGER NOT NULL DEFAULT 1,
            last_run TEXT
        );
        CREATE TABLE IF NOT EXISTS vouchers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            package TEXT NOT NULL,
            code TEXT NOT NULL UNIQUE,
            sold INTEGER NOT NULL DEFAULT 0,
            sold_to INTEGER,
            sold_at TEXT
        );
        CREATE TABLE IF NOT EXISTS orders (
            order_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            order_type TEXT NOT NULL,
            uid TEXT,
            package TEXT,
            price REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL,
            provider_ref TEXT,
            details TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS payments (
            payment_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            method TEXT NOT NULL,
            amount REAL NOT NULL,
            trxid TEXT NOT NULL,
            screenshot_file_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL,
            reviewed_at TEXT,
            reviewed_by INTEGER
        );
        CREATE TABLE IF NOT EXISTS api_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL DEFAULT ''
        );
        """)
        defaults = {
            "bkash": DEFAULT_BKASH,
            "nagad": DEFAULT_NAGAD,
            "maintenance": "0",
            "notice": "",
            "profile_url": "",
            "profile_key": "",
            "topup_url": "",
            "topup_key": "",
        }
        for k, v in defaults.items():
            cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (k, v))
        for k, v in DEFAULT_PRICES.items():
            cur.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", ("price_" + k, str(v)))
        con.commit()
        con.close()


def setting(key, default=""):
    con = db(); row = con.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone(); con.close()
    return row["value"] if row else default

def set_setting(key, value):
    with _db_lock:
        con = db(); con.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)", (key, str(value))); con.commit(); con.close()

def price(key):
    try:
        return float(setting("price_" + key, DEFAULT_PRICES.get(key, 0)))
    except Exception:
        return float(DEFAULT_PRICES.get(key, 0))

def now_bd():
    return datetime.now(timezone(timedelta(hours=6)))

def now_str():
    return now_bd().strftime("%Y-%m-%d %H:%M:%S")

# ============================================================
# USER HELPERS
# ============================================================
def ensure_user(tg_user):
    uid = tg_user.id
    username = tg_user.username or ""
    first_name = tg_user.first_name or "User"
    stamp = now_str()
    with _db_lock:
        con = db()
        row = con.execute("SELECT user_id FROM users WHERE user_id=?", (uid,)).fetchone()
        if row:
            con.execute("UPDATE users SET username=?, first_name=?, last_seen=? WHERE user_id=?", (username, first_name, stamp, uid))
        else:
            con.execute("INSERT INTO users(user_id,username,first_name,created_at,last_seen) VALUES(?,?,?,?,?)", (uid, username, first_name, stamp, stamp))
        con.commit(); con.close()
    return uid

def is_admin(uid):
    return uid in ADMIN_IDS

def blocked(uid):
    con = db(); row = con.execute("SELECT blocked FROM users WHERE user_id=?", (uid,)).fetchone(); con.close()
    return bool(row and row["blocked"])

def get_user(uid):
    con = db(); row = con.execute("SELECT * FROM users WHERE user_id=?", (uid,)).fetchone(); con.close(); return row

def change_balance(uid, amount):
    with _db_lock:
        con = db(); con.execute("UPDATE users SET balance=balance+?, total_added=CASE WHEN ? > 0 THEN total_added+? ELSE total_added END WHERE user_id=?", (amount, amount, amount, uid)); con.commit(); con.close()

def spend_balance(uid, amount):
    with _db_lock:
        con = db(); con.execute("UPDATE users SET balance=balance-?, total_spent=total_spent+? WHERE user_id=?", (amount, amount, uid)); con.commit(); con.close()

# ============================================================
# LIKE API
# ============================================================
def like_request(uid):
    key = LIKE_API_KEY
    url = LIKE_API_URL
    try:
        r = requests.get(url, params={"key": key, "uid": str(uid)}, headers={"User-Agent": "MARUF-FF-BOT/1.0"}, timeout=20)
        try:
            data = r.json()
        except Exception:
            data = {"raw": r.text[:2000]}
        return data, r.status_code
    except Exception as e:
        return {"error": str(e)}, 599

def extract_like_result(data):
    if not isinstance(data, dict):
        return "N/A", "N/A"
    name = data.get("Name") or data.get("player_name") or data.get("Player Nickname") or data.get("nickname") or "N/A"
    likes = data.get("Likes Sent") or data.get("likes_sent") or data.get("likesGiven") or data.get("likes_given") or "N/A"
    return str(name), str(likes)

# ============================================================
# PROFILE API (OPTIONAL, ADMIN CONFIGURED)
# ============================================================
def profile_request(uid, region="BD"):
    url = setting("profile_url", "").strip()
    key = setting("profile_key", "").strip()
    if not url:
        return None, "Profile API not configured. Admin: /setprofileapi URL KEY"
    try:
        headers = {"User-Agent": "MARUF-FF-BOT/1.0"}
        params = {"uid": str(uid), "region": region}
        if key:
            params["key"] = key
            headers["x-api-key"] = key
            headers["Authorization"] = f"Bearer {key}"
        r = requests.get(url, params=params, headers=headers, timeout=20)
        try: data = r.json()
        except Exception: data = {"raw": r.text[:3000]}
        return data, r.status_code
    except Exception as e:
        return None, str(e)

def flatten_profile(data):
    if not isinstance(data, dict): return {}
    candidates = [data, data.get("data", {}), data.get("result", {}), data.get("basicInfo", {})]
    out = {}
    keys = {
        "nickname": ["AccountName", "nickname", "NickName", "player_name", "name"],
        "level": ["AccountLevel", "level", "Level"],
        "region": ["AccountRegion", "region", "Region"],
        "likes": ["AccountLikes", "liked", "likes", "Likes"],
        "exp": ["AccountEXP", "exp", "experience"],
        "last_login": ["AccountLastLogin", "lastLoginAt", "last_login"],
        "created": ["AccountCreateTime", "createAt", "created_at"],
        "br_rank": ["BrMaxRank", "brRank", "rank"],
        "br_points": ["BrRankPoint", "rankingPoints", "brRankPoint"],
        "cs_rank": ["CsMaxRank", "csRank"],
        "cs_points": ["CsRankPoint", "csRankPoint"],
    }
    for dest, names in keys.items():
        for obj in candidates:
            if isinstance(obj, dict):
                for k in names:
                    if k in obj and obj[k] not in (None, ""):
                        out[dest] = obj[k]; break
            if dest in out: break
    return out

# ============================================================
# START / HELP / PUBLIC
# ============================================================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = ensure_user(update.effective_user)
    if blocked(uid):
        await update.effective_message.reply_text("🚫 আপনার অ্যাকাউন্টটি ব্লক করা হয়েছে।")
        return
    notice = setting("notice", "").strip()
    keyboard = [
        [InlineKeyboardButton("🔥 Free Fire Like", callback_data="like_menu"), InlineKeyboardButton("💎 Diamond / Top-up", callback_data="topup_menu")],
        [InlineKeyboardButton("💳 Balance", callback_data="balance"), InlineKeyboardButton("📦 Stock", callback_data="stock")],
        [InlineKeyboardButton("👤 Profile", callback_data="profile_help"), InlineKeyboardButton("📋 My Orders", callback_data="orders")],
        [InlineKeyboardButton("💰 Rate", callback_data="rate"), InlineKeyboardButton("📞 Support", callback_data="support")],
    ]
    if is_admin(uid):
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="admin_panel")])
    text = "👋 <b>স্বাগতম MARUF FF BOT</b>\n\n🔥 Like • 💎 Top-up • 💳 Wallet • 📦 Voucher"
    if notice: text += f"\n\n📢 <b>Notice:</b> {notice}"
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user)
    text = (
        "<b>📜 User Commands</b>\n\n"
        "/start — Main Menu\n/help — Help\n/profile UID — Player profile\n"
        "/like UID — Instant Like\n/add UID Likes Days — Auto Like\n/time HH:MM — Auto Like time\n/list — Active schedules\n/delete ID — Delete schedule\n"
        "/balance — Wallet\n/rate — Price list\n/number — Payment numbers\n/verify TRXID AMOUNT METHOD — Payment request\n"
        "/stock — Voucher stock\n/tp UID PACKAGE — Voucher delivery\n/orders — Order history\n/support — Support\n\n"
        "<b>Admin</b>\n/admin — Admin panel\n/users — Users\n/pending — Pending payments\n"
        "/addbalance USER AMOUNT\n/cutbalance USER AMOUNT\n/setdue USER AMOUNT\n/setadvance USER AMOUNT\n"
        "/addvoucher PACKAGE CODE\n/setrate TYPE PACKAGE PRICE\n/block USER\n/unblock USER\n/broadcast MESSAGE\n"
        "/setpayment bkash|nagad NUMBER\n/setlikeapi URL KEY\n/setprofileapi URL KEY\n/settopupapi URL KEY"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = ensure_user(update.effective_user); u = get_user(uid)
    await update.effective_message.reply_text(
        f"💳 <b>Wallet</b>\n\nBalance: ৳{u['balance']:.2f}\nDue: ৳{u['due']:.2f}\nAdvance: ৳{u['advance']:.2f}\nTotal Spent: ৳{u['total_spent']:.2f}\nTotal Added: ৳{u['total_added']:.2f}", parse_mode=ParseMode.HTML)

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user)
    await update.effective_message.reply_text(f"📞 <b>Support</b>\nTelegram: {TELEGRAM_SUPPORT_USERNAME}\nWhatsApp: {WHATSAPP_NUMBER}", parse_mode=ParseMode.HTML)

async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user)
    await update.effective_message.reply_text(f"💳 <b>Payment Numbers</b>\n\nbKash: <code>{setting('bkash', DEFAULT_BKASH)}</code>\nNagad: <code>{setting('nagad', DEFAULT_NAGAD)}</code>\n\nপেমেন্টের পর /verify TRXID AMOUNT METHOD ব্যবহার করুন।", parse_mode=ParseMode.HTML)

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user)
    text = (
        "💰 <b>Current Rate</b>\n\n"
        f"🔥 Like 7 Days: ৳{price('like_7days'):.0f}\n🔥 Like 30 Days: ৳{price('like_30days'):.0f}\n\n"
        f"💎 25: ৳{price('d25'):.0f}\n💎 50: ৳{price('d50'):.0f}\n💎 115: ৳{price('d115'):.0f}\n💎 240: ৳{price('d240'):.0f}\n💎 610: ৳{price('d610'):.0f}\n"
        f"👑 Weekly: ৳{price('weekly'):.0f}\n👑 Monthly: ৳{price('monthly'):.0f}"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user)
    if not context.args:
        await update.effective_message.reply_text("❌ ব্যবহার: /profile UID [REGION]")
        return
    uid = context.args[0]; region = context.args[1].upper() if len(context.args) > 1 else "BD"
    data, status = profile_request(uid, region)
    if data is None:
        await update.effective_message.reply_text(f"❌ {status}")
        return
    p = flatten_profile(data)
    if not p:
        await update.effective_message.reply_text("❌ Profile API থেকে profile data পাওয়া যায়নি।")
        return
    text = (
        "👤 <b>FREE FIRE PROFILE</b>\n\n"
        f"🆔 UID: <code>{uid}</code>\n📛 Name: <b>{p.get('nickname','N/A')}</b>\n🌍 Region: {p.get('region',region)}\n"
        f"⭐ Level: {p.get('level','N/A')}\n❤️ Likes: {p.get('likes','N/A')}\n🏆 BR Rank: {p.get('br_rank','N/A')} ({p.get('br_points','N/A')})\n"
        f"🎯 CS Rank: {p.get('cs_rank','N/A')} ({p.get('cs_points','N/A')})\n📈 EXP: {p.get('exp','N/A')}\n"
        f"🕒 Last Login: {p.get('last_login','N/A')}\n📅 Created: {p.get('created','N/A')}"
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

# ============================================================
# LIKE / AUTO LIKE
# ============================================================
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_user = ensure_user(update.effective_user)
    if blocked(uid_user): return
    if not context.args:
        await update.effective_message.reply_text("❌ ব্যবহার: /like UID")
        return
    player_uid = context.args[0].strip()
    data, status = like_request(player_uid)
    if status == 200:
        name, likes = extract_like_result(data)
        text = f"🔥 <b>MARUF LIKE BOT</b>\n\n✅ Likes Sent\n🆔 UID: <code>{player_uid}</code>\n📛 Name: <b>{name}</b>\n❤️ Likes: +{likes}"
    else:
        text = f"❌ Like API Error\nHTTP: {status}\n<code>{json.dumps(data, ensure_ascii=False)[:800]}</code>"
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_user = ensure_user(update.effective_user)
    if blocked(uid_user): return
    try:
        player_uid = context.args[0]; likes = int(context.args[1]); days = int(context.args[2].upper().replace("D", ""))
        if likes <= 0 or days <= 0: raise ValueError
    except Exception:
        await update.effective_message.reply_text("❌ ব্যবহার: /add UID Likes Days\nউদাহরণ: /add 123456789 100 7")
        return
    sub_id = os.urandom(3).hex().upper()
    start = now_bd(); end = start + timedelta(days=days)
    with _db_lock:
        con = db(); con.execute("INSERT INTO subscriptions(sub_id,user_id,uid,daily_likes,start_date,end_date) VALUES(?,?,?,?,?,?)", (sub_id, uid_user, player_uid, likes, start.isoformat(), end.isoformat())); con.commit(); con.close()
    await update.effective_message.reply_text(f"✅ <b>Auto Like Added</b>\n\nUID: <code>{player_uid}</code>\nDaily Likes: {likes}\nDays: {days}\nSchedule ID: <code>{sub_id}</code>\nTime: 12:00", parse_mode=ParseMode.HTML)

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_user = ensure_user(update.effective_user)
    if not context.args:
        await update.effective_message.reply_text("❌ /delete SCHEDULE_ID")
        return
    sid = context.args[0].upper()
    with _db_lock:
        con = db(); cur = con.execute("UPDATE subscriptions SET active=0 WHERE sub_id=? AND user_id=?", (sid, uid_user)); con.commit(); con.close()
    await update.effective_message.reply_text("🗑️ Schedule deleted." if cur.rowcount else "❌ Schedule পাওয়া যায়নি।")

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_user = ensure_user(update.effective_user)
    con = db(); rows = con.execute("SELECT * FROM subscriptions WHERE user_id=? AND active=1 ORDER BY created_at DESC", (uid_user,)).fetchall(); con.close()
    if not rows:
        await update.effective_message.reply_text("📋 কোনো active schedule নেই।"); return
    text = "📋 <b>Active Schedules</b>\n\n"
    for r in rows:
        text += f"🆔 <code>{r['sub_id']}</code> | UID {r['uid']} | {r['daily_likes']}/day | {r['auto_time']}\n"
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid_user = ensure_user(update.effective_user)
    if not context.args or not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", context.args[0]):
        await update.effective_message.reply_text("❌ সময় দিন HH:MM format-এ, যেমন /time 18:30"); return
    t = context.args[0]
    with _db_lock:
        con = db(); con.execute("UPDATE subscriptions SET auto_time=? WHERE user_id=? AND active=1", (t, uid_user)); con.commit(); con.close()
    await update.effective_message.reply_text(f"⏰ Active Auto Like-এর সময় {t} সেট হয়েছে।")

async def auto_like_checker(application):
    while True:
        try:
            current = now_bd()
            hhmm = current.strftime("%H:%M")
            con = db(); rows = con.execute("SELECT * FROM subscriptions WHERE active=1 AND auto_time=?", (hhmm,)).fetchall(); con.close()
            for r in rows:
                try:
                    end = datetime.fromisoformat(r["end_date"])
                    if current > end:
               
