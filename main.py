import os
import sqlite3
import threading
from datetime import datetime
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

BOT_TOKEN = os.getenv("8915748936:AAFtZ08QQ-_BBvrwjMydusssz9A5e1ME6i0", "")
LIKE_API_KEY = os.getenv("LIKE_API_KEY"VALT2H", "")
LIKE_API_URL = os.getenv("LIKE_API_URL", "https://api.freefirelike.com/like")

ADMIN_IDS = {6347427263, 6992868111}
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"
WHATSAPP_NUMBER = "01618203922"
DEFAULT_BKASH = "01618203922"
DEFAULT_NAGAD = "01842408034"
DB_PATH = os.getenv("DB_PATH", "bot.db")

lock = threading.Lock()

def conn():
    c=sqlite3.connect(DB_PATH, check_same_thread=False)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    with lock:
        c=conn()
        c.execute("""CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
            balance REAL DEFAULT 0, due REAL DEFAULT 0, advance REAL DEFAULT 0,
            total_payment REAL DEFAULT 0, total_spending REAL DEFAULT 0,
            created_at TEXT)""")
        c.execute("""CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY, value TEXT)""")
        for k,v in {"bkash":DEFAULT_BKASH,"nagad":DEFAULT_NAGAD}.items():
            c.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",(k,v))
        c.commit(); c.close()

def setting(k, default=""):
    with lock:
        c=conn(); r=c.execute("SELECT value FROM settings WHERE key=?",(k,)).fetchone(); c.close()
    return r["value"] if r else default

def set_setting(k,v):
    with lock:
        c=conn(); c.execute("""INSERT INTO settings(key,value) VALUES(?,?)
        ON CONFLICT(key) DO UPDATE SET value=excluded.value""",(k,v)); c.commit(); c.close()

def save_user(u):
    with lock:
        c=conn(); c.execute("""INSERT INTO users(user_id,username,first_name,created_at)
        VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET
        username=excluded.username, first_name=excluded.first_name""",
        (u.id,u.username or "",u.first_name or "",datetime.utcnow().isoformat()))
        c.commit(); c.close()

def get_user(uid):
    with lock:
        c=conn(); r=c.execute("SELECT * FROM users WHERE user_id=?",(uid,)).fetchone(); c.close()
    return r

web=Flask(__name__)
@web.route("/")
def home(): return "MARUF FF BOT is running."
@web.route("/health")
def health(): return {"status":"ok"}

def run_web():
    web.run(host="0.0.0.0",port=int(os.getenv("PORT","10000")))

def menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👤 Account",callback_data="account"),
         InlineKeyboardButton("💰 Balance",callback_data="balance")],
        [InlineKeyboardButton("❤️ Like",callback_data="like"),
         InlineKeyboardButton("🔎 UID Info",callback_data="uid")],
        [InlineKeyboardButton("💳 Add Balance",callback_data="add"),
         InlineKeyboardButton("📞 Support",callback_data="support")]
    ])

def admin_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("👥 Users",callback_data="users"),
         InlineKeyboardButton("⚙️ Settings",callback_data="settings")],
        [InlineKeyboardButton("💵 bKash",callback_data="bkash"),
         InlineKeyboardButton("💵 Nagad",callback_data="nagad")]
    ])

async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    save_user(update.effective_user)
    await update.message.reply_text("👋 Welcome to MARUF FF BOT!\n\nChoose an option:",reply_markup=menu())

async def help_cmd(update,context):
    save_user(update.effective_user)
    await update.message.reply_text("/start\n/balance\n/like UID\n/uid UID\n/support\n/admin")

async def balance(update,context):
    save_user(update.effective_user); r=get_user(update.effective_user.id)
    await update.message.reply_text(f"💰 Balance: {r['balance']:.2f}\n📌 Due: {r['due']:.2f}\n➕ Advance: {r['advance']:.2f}\n💳 Payment: {r['total_payment']:.2f}\n🛒 Spending: {r['total_spending']:.2f}")

async def support(update,context):
    save_user(update.effective_user)
    await update.message.reply_text(f"📞 Telegram: {TELEGRAM_SUPPORT_USERNAME}\n📱 WhatsApp: {WHATSAPP_NUMBER}")

async def admin(update,context):
    save_user(update.effective_user)
    if update.effective_user.id not in ADMIN_IDS:
        return await update.message.reply_text("❌ Admin only.")
    await update.message.reply_text("🛠 Admin Panel",reply_markup=admin_menu())

async def users(update,context):
    if update.effective_user.id not in ADMIN_IDS: return
    with lock:
        c=conn(); rows=c.execute("SELECT user_id,username,first_name,balance FROM users ORDER BY created_at DESC").fetchall(); c.close()
    if not rows: return await update.message.reply_text("No users.")
    text="👥 Users\n\n"
    for r in rows:
        text += f"{r['first_name'] or '-'} | @{r['username'] or '-'}\nID: {r['user_id']} | Balance: {r['balance']:.2f}\n\n"
    await update.message.reply_text(text[:4000])

async def callbacks(update,context):
    q=update.callback_query; await q.answer(); u=update.effective_user; save_user(u)
    d=q.data
    if d=="account":
        r=get_user(u.id); return await q.edit_message_text(f"👤 Account\n\nName: {r['first_name']}\nID: {r['user_id']}\nBalance: {r['balance']:.2f}\nDue: {r['due']:.2f}\nAdvance: {r['advance']:.2f}")
    if d=="balance":
        r=get_user(u.id); return await q.edit_message_text(f"💰 Balance: {r['balance']:.2f}\n📌 Due: {r['due']:.2f}\n➕ Advance: {r['advance']:.2f}")
    if d=="support":
        return await q.edit_message_text(f"📞 Telegram: {TELEGRAM_SUPPORT_USERNAME}\n📱 WhatsApp: {WHATSAPP_NUMBER}")
    if d=="add":
        return await q.edit_message_text(f"💳 Add Balance\n\nbKash: {setting('bkash',DEFAULT_BKASH)}\nNagad: {setting('nagad',DEFAULT_NAGAD)}")
    if d=="like":
        return await q.edit_message_text("❤️ Use: /like YOUR_UID")
    if d=="uid":
        return await q.edit_message_text("🔎 Use: /uid YOUR_UID")
    if u.id not in ADMIN_IDS: return
    if d=="users":
        with lock:
            c=conn(); rows=c.execute("SELECT user_id,username,first_name,balance FROM users ORDER BY created_at DESC").fetchall(); c.close()
        text="👥 Users\n\n"+''.join(f"{r['first_name'] or '-'} | @{r['username'] or '-'} | {r['user_id']} | {r['balance']:.2f}\n" for r in rows)
        return await q.edit_message_text(text[:4000] or "No users.")
    if d=="settings":
        return await q.edit_message_text(f"⚙️ Settings\nbKash: {setting('bkash')}\nNagad: {setting('nagad')}")
    if d in ("bkash","nagad"):
        context.user_data["setting"]=d; return await q.edit_message_text(f"Send new {d} number.")

async def text(update,context):
    save_user(update.effective_user)
    k=context.user_data.get("setting")
    if k and update.effective_user.id in ADMIN_IDS:
        set_setting(k,update.message.text.strip()); context.user_data.pop("setting",None)
        await update.message.reply_text(f"✅ {k.upper()} updated.")

async def like(update,context):
    save_user(update.effective_user)
    if not context.args: return await update.message.reply_text("Use: /like UID")
    if not LIKE_API_KEY: return await update.message.reply_text("⚠️ LIKE_API_KEY is not configured in Render.")
    import requests
    try:
        r=requests.get(LIKE_API_URL,params={"key":LIKE_API_KEY,"uid":context.args[0]},timeout=20)
        if r.status_code!=200: return await update.message.reply_text(f"❌ API HTTP {r.status_code}")
        d=r.json()
        name=d.get("Name") or d.get("player_name") or d.get("Player Nickname") or "Unknown"
        likes=d.get("Likes Sent") or d.get("likes_given") or d.get("Likes") or d.get("likes") or "N/A"
        await update.message.reply_text(f"❤️ LIKE RESULT\n\nUID: {context.args[0]}\nName: {name}\nLikes Sent: {likes}")
    except Exception as e:
        await update.message.reply_text(f"❌ Like request failed: {str(e)[:300]}")

async def uid(update,context):
    save_user(update.effective_user)
    await update.message.reply_text("🔎 Profile API is not configured yet.")

def main():
    init_db()
    if not BOT_TOKEN: raise RuntimeError("BOT_TOKEN is missing. Add it in Render Environment Variables.")
    threading.Thread(target=run_web,daemon=True).start()
    app=Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",start))
    app.add_handler(CommandHandler("help",help_cmd))
    app.add_handler(CommandHandler("balance",balance))
    app.add_handler(CommandHandler("support",support))
    app.add_handler(CommandHandler("admin",admin))
    app.add_handler(CommandHandler("users",users))
    app.add_handler(CommandHandler("like",like))
    app.add_handler(CommandHandler("uid",uid))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,text))
    print("MARUF FF BOT started")
    app.run_polling(drop_pending_updates=True)

if __name__=="__main__":
    main()
    
