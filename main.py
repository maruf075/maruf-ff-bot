import os
import asyncio
import requests
from threading import Thread
from flask import Flask
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- 1. Render Port Scan Fix (Web Server for Free Instance) ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is running perfectly 24/7 on Free Tier!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

# --- 2. Configurations & Variables ---
BOT_TOKEN = "8915748936:AAGPXAt0h-7tWOPpumGWrzoYejXf3xRPHJQ"
LIKE_API_KEY = "VALT2H"

ADMIN_IDS = [6347427263, 6992868111]  
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"  
WHATSAPP_NUMBER = "+8801618203922"              

user_balances = {}
active_subscriptions = {}
user_api_keys = {}

item_prices = {
    "d25": 20, "d50": 35, "d115": 80, "d240": 160, "d610": 400,
    "weekly": 160, "monthly": 800, "like_7days": 50, "like_30days": 180
}

vouchers_stock = {
    "25": [], "50": [], "115": [], "240": [], "610": [], "weekly": [], "monthly": []
}

# --- 3. API & Auto Checker Loop ---
def send_like_request(api_key, uid):
    endpoints = [
        f"https://key.like.mlbbshop.com/like?key={api_key}&uid={uid}",
        f"https://freefirelike.com/api/like?key={api_key}&uid={uid}",
        f"https://buykey.freefirelike.com/like?key={api_key}&uid={uid}"
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                return res.json(), 200
        except Exception:
            continue
    return None, 404

async def auto_like_checker(telegram_app):
    while True:
        try:
            bd_now = datetime.utcnow() + timedelta(hours=6)
            current_time_str = bd_now.strftime("%H:%M")

            for user_id, subs in list(active_subscriptions.items()):
                api_key_to_use = user_api_keys.get(user_id, LIKE_API_KEY)

                for sub in list(subs):
                    if bd_now > sub["end_date"]:
                        subs.remove(sub)
                        continue

                    if sub["auto_time"] == current_time_str:
                        uid = sub["uid"]
                        data, status = send_like_request(api_key_to_use, uid)
                        time_now_str = bd_now.strftime("%I:%M %p, %d %b %Y")

                        if status == 200 and data:
                            name = data.get("Name") or data.get("player_name") or "N/A"
                            likes_given = data.get("Likes Sent") or 100
                            msg = f"⏰ **[AUTO LIKE SENT]**\n\n👤 **UID:** `{uid}`\n📛 **Name:** `{name}`\n❤️ **Likes:** +{likes_given}\n🕒 `{time_now_str}`"
                        else:
                            msg = f"⏰ **[AUTO LIKE FAILED]**\n🎯 **UID:** `{uid}`"

                        try:
                            await telegram_app.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
                        except Exception:
                            pass
        except Exception:
            pass
        await asyncio.sleep(30)

# --- 4. Bot Command List Setup ---
async def set_bot_commands(application):
    commands = [
        BotCommand("start", "বট চালু করুন"),
        BotCommand("help", "সকল কমান্ডের তালিকা"),
        BotCommand("key", "API Key সেট করুন"),
        BotCommand("support", "সাপোর্ট তথ্য"),
        BotCommand("number", "পেমেন্ট নম্বর"),
        BotCommand("rate", "লাইকের রেট লিস্ট"),
        BotCommand("balance", "ওয়ালেট ব্যালেন্স"),
        BotCommand("verify", "ট্রানজেকশন ভেরিফাই করুন"),
        BotCommand("add", "লাইক প্যাকেজ যোগ করুন"),
        BotCommand("delete", "শেডিউল ডিলিট করুন"),
        BotCommand("usage", "API Usage বিবরণ"),
        BotCommand("list", "অ্যাক্টিভ শেডিউলের তালিকা"),
        BotCommand("time", "অটো টাইম সেট করুন"),
        BotCommand("like", "ইনস্ট্যান্ট লাইক পাঠান"),
        BotCommand("stock", "UniPin ভাউচার স্টক দেখুন"),
        BotCommand("tp", "ডায়মন্ড ও মেম্বারশিপ টপ-আপ করুন"),
        BotCommand("topup", "ডায়মন্ড ও মেম্বারশিপ টপ-আপ করুন"),
        BotCommand("addvoucher", "[Admin] ভাউচার এড করুন"),
        BotCommand("setrate", "[Admin] দাম পরিবর্তন করুন"),
        BotCommand("addbalance", "[Admin] ব্যালেন্স যোগ করুন"),
        BotCommand("cutbalance", "[Admin] ব্যালেন্স কাটুন"),
        BotCommand("admin", "অ্যাডমিন প্যানেল"),
    ]
    await application.bot.set_my_commands(commands)

# --- 5. User Command Functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_balances:
        user_balances[user_id] = 0.0

    keyboard = [
        [InlineKeyboardButton("🔥 Free Fire Like", callback_data='ff_like'),
         InlineKeyboardButton("💎 Free Fire Diamond", callback_data='ff_diamond')],
        [InlineKeyboardButton("💳 My Balance", callback_data='my_balance'),
         InlineKeyboardButton("📦 Stock Check", callback_data='check_stock')],
        [InlineKeyboardButton("📞 Support", callback_data='support')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 স্বাগতম মারুফ লাইক ও টপ-আপ বটে! সকল কমান্ড একসাথে দেখতে /help টাইপ করুন।", reply_markup=reply_markup)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📜 **বটের সকল কমান্ডের তালিকা:**\n\n"
        "• /key `[KEY]` - API Key সেট করুন\n"
        "• /help - সকল কমান্ডের তালিকা দেখাবে\n"
        "• /support - কাস্টমার সাপোর্ট তথ্য\n"
        "• /number - বিকাশ/নগদ পেমেন্ট নম্বর\n"
        "• /rate - লাইক ও ডায়মন্ডের দামের তালিকা\n"
        "• /balance - ওয়ালেটের বর্তমান ব্যালেন্স\n"
        "• /stock - UniPin ভাউচারের বর্তমান স্টক দেখুন\n"
        "• /tp `[UID] [Package]` - ডায়মন্ড/মেম্বারশিপ টপ-আপ করুন\n"
        "• /verify `[TrxID]` - টাকা জমা দিয়ে ব্যালেন্স যুক্ত করুন\n"
        "• /add `[UID] [Likes] [Days]` - অটো-লাইক প্যাকেজ যোগ করুন\n"
        "• /delete `[Schedule_ID]` - রানিং শেডিউল ডিলিট করুন\n"
        "• /usage - API Key ব্যবহারের বিবরণ\n"
        "• /list - অ্যাক্টিভ শেডিউলের তালিকা\n"
        "• /time `[HH:MM]` - অটো-লাইকের সময় সেট করুন\n"
        "• /like `[UID]` - ইনস্ট্যান্ট লাইক পাঠান\n\n"
        "⚙️ **অ্যাডমিন কমান্ডসমূহ:**\n"
        "• /addbalance `[User_ID] [Amount]` - ব্যালেন্স যোগ করুন\n"
        "• /cutbalance `[User_ID] [Amount]` - ব্যালেন্স কাটুন\n"
        "• /addvoucher `[Pkg] [Code]` - স্টক যোগ করুন\n"
        "• /setrate `[Type] [Pkg] [Price]` - দাম পরিবর্তন করুন\n"
        "• /admin - অ্যাডমিন কন্ট্রোল প্যানেল\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        current_key = user_api_keys.get(user_id, LIKE_API_KEY)
        await update.message.reply_text(f"🔑 **আপনার বর্তমান API Key:** `{current_key}`\n\nনতুন Key সেট করতে টাইপ করুন:\n`/key YOUR_API_KEY`", parse_mode='Markdown')
        return
    new_key = context.args[0].strip()
    user_api_keys[user_id] = new_key
    await update.message.reply_text(f"✅ সফলভাবে আপনার নতুন **API Key** সেট করা হয়েছে!\n🔑 **Key:** `{new_key}`", parse_mode='Markdown')

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"📞 **Customer Support:**\nTelegram: {TELEGRAM_SUPPORT_USERNAME}\nWhatsApp: {WHATSAPP_NUMBER}"
    await update.message.reply_text(msg)

async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💳 **Payment Numbers:**\nbKash/Nagad Personal: `01618203922`"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "💰 **Current Price List:**\n\n"
        "🔥 **Free Fire Likes:**\n"
        f"• 100 Likes/Day (7 Days): ৳{item_prices['like_7days']}\n"
        f"• 100 Likes/Day (30 Days): ৳{item_prices['like_30days']}\n\n"
        "💎 **Diamonds & Memberships (UniPin):**\n"
        f"• 25 Diamonds: ৳{item_prices['d25']}\n"
        f"• 50 Diamonds: ৳{item_prices['d50']}\n"
        f"• 115 Diamonds: ৳{item_prices['d115']}\n"
        f"• 240 Diamonds: ৳{item_prices['d240']}\n"
        f"• 610 Diamonds: ৳{item_prices['d610']}\n"
        f"• Weekly Membership: ৳{item_prices['weekly']}\n"
        f"• Monthly Membership: ৳{item_prices['monthly']}"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)
    await update.message.reply_text(f"💳 আপনার বর্তমান ওয়ালেট ব্যালেন্স: **৳{bal}**", parse_mode='Markdown')

async def verify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ট্রানজেকশন আইডি প্রদান করুন! উদাহরণ: `/verify 9X82K10L`", parse_mode='Markdown')
        return
    await update.message.reply_text("⏳ আপনার ট্রানজেকশন ভেরিফাই করা হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন।")

async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        uid = context.args[0]
        likes = int(context.args[1])
        days_str = context.args[2].upper().replace("D", "")
        days = int(days_str)
        user_id = update.effective_user.id
        end_date = datetime.now() + timedelta(days=days)
        sub_id = os.urandom(3).hex().upper()

        if user_id not in active_subscriptions:
            active_subscriptions[user_id] = []

        active_subscriptions[user_id].append({
            "sub_id": sub_id, "uid": uid, "daily_likes": likes,
            "start_date": datetime.now(), "end_date": end_date,
            "total_days": days, "used_likes": 0, "auto_time": "12:00"
        })
        await update.message.reply_text(f"✅ সফলভাবে **{days} দিনের** লাইক প্যাকেজ যোগ করা হয়েছে!\n🎯 **UID:** `{uid}`\n🔥 **দৈনিক লাইক:** {likes}\n🆔 **Schedule ID:** `{sub_id}`", parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/add [UID] [Likes] [Days]`", parse_mode='Markdown')

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Schedule ID দিন! উদাহরণ: `/delete 2D7919`", parse_mode='Markdown')
        return
    sub_id = context.args[0].strip().upper()
    user_id = update.effective_user.id
    subs = active_subscriptions.get(user_id, [])
    active_subscriptions[user_id] = [s for s in subs if s['sub_id'] != sub_id]
    await update.message.reply_text(f"🗑️ Schedule ID `{sub_id}` সফলভাবে ডিলিট করা হয়েছে।", parse_mode='Markdown')

async def stock_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "📦 **UniPin Voucher Stock Status:**\n\n"
        f"💎 **25 Diamonds:** {len(vouchers_stock['25'])} Pcs\n"
        f"💎 **50 Diamonds:** {len(vouchers_stock['50'])} Pcs\n"
        f"💎 **115 Diamonds:** {len(vouchers_stock['115'])} Pcs\n"
        f"💎 **240 Diamonds:** {len(vouchers_stock['240'])} Pcs\n"
        f"💎 **610 Diamonds:** {len(vouchers_stock['610'])} Pcs\n"
        f"👑 **Weekly Membership:** {len(vouchers_stock['weekly'])} Pcs\n"
        f"👑 **Monthly Membership:** {len(vouchers_stock['monthly'])} Pcs\n\n"
        "💡 *টপ-আপ করতে `/tp [UID] [Package]` কমান্ড ব্যবহার করুন।*"
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def topup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ সঠিক নিয়ম: `/tp [Player_UID] [Package]`\nউদাহরণ: `/tp 12345678 115`", parse_mode='Markdown')
            return
        uid = context.args[0].strip()
        pkg = context.args[1].lower().strip()
        pkg_key = f"d{pkg}" if pkg in ["25", "50", "115", "240", "610"] else pkg

        if pkg not in vouchers_stock:
            await update.message.reply_text("❌ ভুল প্যাকেজ নাম!", parse_mode='Markdown')
            return
        if len(vouchers_stock[pkg]) == 0:
            await update.message.reply_text(f"❌ দুঃখিত! **{pkg.upper()}** প্যাকেজটি আউট অফ স্টক।", parse_mode='Markdown')
            return

        price = item_prices.get(pkg_key, 0)
        user_bal = user_balances.get(user_id, 0.0)

        if user_bal < price:
            await update.message.reply_text(f"❌ পর্যাপ্ত ব্যালেন্স নেই!", parse_mode='Markdown')
            return

        user_balances[user_id] -= price
        code = vouchers_stock[pkg].pop(0)
        bd_now = datetime.utcnow() + timedelta(hours=6)
        time_str = bd_now.strftime("%I:%M %p, %d %b %Y")

        msg = (
            "💎 **[TOP-UP VOUCHER DELIVERED]**\n\n"
            f"👤 **Player UID:** `{uid}`\n"
            f"📦 **Package:** {pkg.upper()}\n"
            f"💰 **Deducted:** ৳{price}\n\n"
            f"🎟️ **UniPin Voucher Code:**\n`{code}`\n\n"
            "🔗 **Redeem Link:** https://shop.garena.my\n"
            f"🕒 `{time_str}`"
        )
        await update.message.reply_text(msg, parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ সঠিক নিয়ম: `/tp [Player_UID] [Package]`", parse_mode='Markdown')

# --- 6. Admin Commands ---
async def addbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        current_bal = user_balances.get(target_id, 0.0)
        new_bal = current_bal + amount
        user_balances[target_id] = new_bal
        await update.message.reply_text(f"✅ ইউজার `{target_id}`-এর ওয়ালেটে **৳{amount}** যোগ করা হয়েছে।\nবর্তমান ব্যালেন্স: **৳{new_bal}**", parse_mode='Markdown')
        try:
            await context.bot.send_message(chat_id=target_id, text=f"🎉 আপনার ওয়ালেটে **৳{amount}** অ্যাডমিন কর্তৃক যুক্ত করা হয়েছে!\nবর্তমান ব্যালেন্স: **৳{new_bal}**", parse_mode='Markdown')
        except Exception:
            pass
    except Exception:
        await update.message.reply_text("❌ সঠিক নিয়ম: `/addbalance [User_ID] [Amount]`", parse_mode='Markdown')

async def cutbalance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        target_id = int(context.args[0])
        amount = float(context.args[1])
        current_bal = user_balances.get(target_id, 0.0)
        new_bal = max(0.0, current_bal - amount)
        user_balances[target_id] = new_bal
        await update.message.reply_text(f"✂️ ইউজার `{target_id}`-এর ওয়ালেট থেকে **৳{amount}** কাটা হয়েছে।\nবর্তমান ব্যালেন্স: **৳{new_bal}**", parse_mode='Markdown')
        try:
            await context.bot.send_message(chat_id=target_id, text=f"⚠️ আপনার ওয়ালেট থেকে **৳{amount}** কাটা হয়েছে।\nবর্তমান ব্যালেন্স: **৳{new_bal}**", parse_mode='Markdown')
        except Exception:
            pass
    except Exception:
        await update.message.reply_text("❌ সঠিক নিয়ম: `/cutbalance [User_ID] [Amount]`", parse_mode='Markdown')

async def addvoucher_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        pkg = context.args[0].lower()
        code = context.args[1].strip()
        if pkg in vouchers_stock:
            vouchers_stock[pkg].append(code)
            await update.message.reply_text(f"✅ **{pkg}** এ নতুন ভাউচার যোগ হয়েছে!", parse_mode='Markdown')
    except Exception:
        pass

async def setrate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return
    try:
        category, target, new_price = context.args[0].lower(), context.args[1].lower(), float(context.args[2])
        if category == "diamond":
            key = f"d{target}" if target in ["25", "50", "115", "240", "610"] else target
            item_prices[key] = new_price
        elif category == "like":
            item_prices[f"like_{target}"] = new_price
        await update.message.reply_text("✅ দাম আপডেট করা হয়েছে।")
    except Exception:
        pass

# --- 7. Utility & Callback Functions ---
async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    api_key_to_use = user_api_keys.get(user_id, LIKE_API_KEY)
    data, status = send_like_request(api_key_to_use, "100000000")
    daily_rem = data.get("Daily Remaining", "N/A") if data else "N/A"
    msg = f"🔑 **API Usage Details**\n👤 Username: {user_name}\n🔑 Key: `{api_key_to_use}`\n⚡ Daily Remaining: {daily_rem}"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in active_subscriptions and active_subscriptions[user_id] and context.args:
        parsed_time = context.args[0].strip()
        for sub in active_subscriptions[user_id]:
            sub["auto_time"] = parsed_time
        await update.message.reply_text(f"⏰ অটো লাইকের সময় **{parsed_time}** সেট করা হয়েছে।")

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return
    user_id = update.effective_user.id
    api_key_to_use = user_api_keys.get(user_id, LIKE_API_KEY)
    uid = str(context.args[0]).strip()
    data, status = send_like_request(api_key_to_use, uid)
    if status == 200 and data:
        name = data.get("Name") or "N/A"
        likes_given = data.get("Likes Sent") or 100
        msg = f"🔥 **MARUF LIKE BOT**\n\n✅ **Likes Sent!**\n👤 **UID:** `{uid}`\n📛 **Name:** `{name}`\n❤️ **Likes:** +{likes_given}"
    else:
        msg = "❌ API Error!"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subs = active_subscriptions.get(user_id, [])
    if not subs:
        await update.message.reply_text("📋 কোনো সক্রিয় শেডিউল পাওয়া যায়নি।")
        return
    msg = "📋 **Active Schedules:**\n"
    for idx, sub in enumerate(subs, 1):
        msg += f"{idx}. UID: `{sub['uid']}` | Time: `{sub['auto_time']}`\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id in ADMIN_IDS:
        await update.message.reply_text("⚙️ **Admin Panel Active!**")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == 'check_stock':
        await stock_command(query, context)

async def post_init(application):
    await set_bot_commands(application)
    asyncio.create_task(auto_like_checker(application))

# --- 8. Main Function ---
def main():
    # Flask ওয়েব সার্ভার চালু করা (Render Web Service Port Detection Fix)
    server_thread = Thread(target=run_flask)
    server_thread.daemon = True
    server_thread.start()

    telegram_app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("key", key_command))
    telegram_app.add_handler(CommandHandler("support", support_command))
    telegram_app.add_handler(CommandHandler("number", number_command))
    telegram_app.add_handle
