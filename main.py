import os
import asyncio
import requests
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8915748936:AAGPXAt0h-7tWOPpumGWrzoYejXf3xRPHJQ"
LIKE_API_KEY = "VALT2H"

ADMIN_IDS = [6347427263, 6992868111]  
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"  
WHATSAPP_NUMBER = "+8801618203922"              

user_balances = {}
active_subscriptions = {}
user_api_keys = {}

app = Flask(__name__)
telegram_app = None

@app.route('/')
def home():
    return "Bot is Live and Running 24/7!"

def send_like_request(api_key, uid):
    """API থেকে লাইক পাঠানোর জন্য মাল্টিপল এ্যান্ডপয়েন্ট ট্রাই করার ফাংশন"""
    endpoints = [
        f"https://key.like.mlbbshop.com/like?key={api_key}&uid={uid}",
        f"https://freefirelike.com/api/like?key={api_key}&uid={uid}",
        f"https://buykey.freefirelike.com/like?key={api_key}&uid={uid}"
    ]
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for url in endpoints:
        try:
            res = requests.get(url, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.json(), 200
        except Exception:
            continue
            
    return None, 404

async def auto_like_checker():
    """অটোমেটিক লাইক চেকার টাস্ক"""
    while True:
        try:
            if telegram_app:
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
                                name = data.get("Name") or data.get("player_name") or data.get("name") or "N/A"
                                likes_given = data.get("Likes Sent") or data.get("likes_given") or 100
                                before = data.get("Before") or data.get("likes_before") or "N/A"
                                after = data.get("After") or data.get("likes_after") or "N/A"
                                
                                if likes_given or str(data.get("status", "")).lower() == "success":
                                    sub["used_likes"] += int(likes_given)
                                    msg = (
                                        "⏰ **[AUTO LIKE SENT]**\n\n"
                                        "🔥 **MARUF LIKE BOT**\n"
                                        f"👤 **UID:** `{uid}`\n"
                                        f"📛 **Name:** `{name}`\n"
                                        f"❤️ **Likes Sent:** +{likes_given}\n"
                                        f"📊 **Before:** {before}\n"
                                        f"📈 **After:** {after}\n\n"
                                        f"🕒 `{time_now_str}`"
                                    )
                                else:
                                    reason = data.get("Reason") or data.get("message") or "Limit reached for today"
                                    msg = (
                                        "⏰ **[AUTO LIKE FAILED]**\n\n"
                                        f"🎯 **UID:** `{uid}`\n"
                                        f"❌ **Reason:** {reason}\n\n"
                                        f"🕒 `{time_now_str}`"
                                    )
                            else:
                                msg = f"❌ **Auto Like Error!** API Server Response Fail."

                            try:
                                await telegram_app.bot.send_message(chat_id=user_id, text=msg, parse_mode='Markdown')
                            except Exception:
                                pass
        except Exception:
            pass
        
        await asyncio.sleep(30)

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
        BotCommand("list", "অ্যাক্টিভ শেডিউল লিস্ট"),
        BotCommand("time", "অটো টাইম সেট করুন"),
        BotCommand("like", "ইনস্ট্যান্ট লাইক পাঠান"),
        BotCommand("admin", "অ্যাডমিন প্যানেল"),
    ]
    await application.bot.set_my_commands(commands)

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
    await update.message.reply_text("স্বাগতম মারুফ লাইক বটে! সকল কমান্ড একসাথে দেখতে /help টাইপ করুন।", reply_markup=reply_markup)

async def key_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        current_key = user_api_keys.get(user_id, LIKE_API_KEY)
        await update.message.reply_text(f"🔑 **আপনার বর্তমান API Key:** `{current_key}`\n\nনতুন Key সেট করতে টাইপ করুন:\n`/key YOUR_API_KEY`", parse_mode='Markdown')
        return

    new_key = context.args[0].strip()
    user_api_keys[user_id] = new_key
    await update.message.reply_text(f"✅ সফলভাবে আপনার নতুন **API Key** সেট করা হয়েছে!\n🔑 **Key:** `{new_key}`", parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📜 **বটের সকল কমান্ডের তালিকা:**\n\n"
        "• /key `[KEY]` - API Key সেট করুন\n"
        "• /help - সকল কমান্ডের তালিকা দেখাবে\n"
        "• /support - কাস্টমার সাপোর্ট তথ্য দেখাবে\n"
        "• /number - বিকাশ/নগদ পেমেন্ট নম্বর\n"
        "• /rate - লাইকের অফার ও দামের তালিকা\n"
        "• /balance - ওয়ালেটের বর্তমান ব্যালেন্স\n"
        "• /verify `[TrxID]` - টাকা জমা দিয়ে ব্যালেন্স যুক্ত করুন\n"
        "• /add `[UID] [Likes] [Days]` - অটো-লাইক প্যাকেজ যোগ করুন\n"
        "• /delete `[Schedule_ID]` - রানিং শেডিউল ডিলিট করুন\n"
        "• /usage - API Key ব্যবহারের বিস্তারিত বিবরণ\n"
        "• /list - অ্যাক্টিভ শেডিউলের তালিকা\n"
        "• /time `[HH:MM]` - প্রতিদিন অটো-লাইক যাওয়ার সময় সেট করুন\n"
        "• /like `[UID]` - ইনস্ট্যান্ট লাইক পাঠান\n"
        "• /admin - অ্যাডমিন কন্ট্রোল প্যানেল\n"
    )
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def support_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = f"📞 **Customer Support:**\nTelegram: {TELEGRAM_SUPPORT_USERNAME}\nWhatsApp: {WHATSAPP_NUMBER}"
    await update.message.reply_text(msg)

async def number_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "💳 **Payment Numbers:**\nbKash/Nagad Personal: `01618203922`"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def rate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = "🔥 **Like Offer Rates:**\n• 100 Likes/Day (7 Days) - 50 BDT\n• 100 Likes/Day (30 Days) - 180 BDT"
    await update.message.reply_text(msg)

async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = user_balances.get(user_id, 0.0)
    await update.message.reply_text(f"💳 আপনার বর্তমান ওয়ালেট ব্যালেন্স: **{bal} BDT**", parse_mode='Markdown')

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
            "sub_id": sub_id,
            "uid": uid,
            "daily_likes": likes,
            "start_date": datetime.now(),
            "end_date": end_date,
            "total_days": days,
            "used_likes": 0,
            "auto_time": "12:00"
        })
        await update.message.reply_text(f"✅ সফলভাবে **{days} দিনের** লাইক প্যাকেজ যোগ করা হয়েছে!\n🎯 **UID:** `{uid}`\n🔥 **দৈনিক লাইক:** {likes}\n🆔 **Schedule ID:** `{sub_id}`", parse_mode='Markdown')
    except Exception:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/add [UID] [Likes] [Days]`\nউদাহরণ: `/add 12345678 100 30D`", parse_mode='Markdown')

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Schedule ID দিন! উদাহরণ: `/delete 2D7919`", parse_mode='Markdown')
        return
    sub_id = context.args[0].strip().upper()
    user_id = update.effective_user.id
    subs = active_subscriptions.get(user_id, [])
    
    active_subscriptions[user_id] = [s for s in subs if s['sub_id'] != sub_id]
    await update.message.reply_text(f"🗑️ Schedule ID `{sub_id}` সফলভাবে ডিলিট করা হয়েছে।", parse_mode='Markdown')

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name or "User"
    api_key_to_use = user_api_keys.get(user_id, LIKE_API_KEY)
    
    bd_now = datetime.utcnow() + timedelta(hours=6)
    current_time_str = bd_now.strftime("%I:%M %p, %d %b %Y")

    # একটি টেস্ট রিকোয়েস্ট পাঠাবো API এর স্ট্যাটাস ও লিমিট চেক করতে
    test_uid = "100000000"
    data, status = send_like_request(api_key_to_use, test_uid)

    daily_rem = "N/A"
    status_text = "🟢 Active" if status == 200 else "🔴 Inactive/Error"

    if data:
        daily_rem = data.get("Daily Remaining") or data.get("daily_remaining") or "N/A"

    msg = (
        "🔑 **API Key Usage Details**\n\n"
        f"👤 **Username:** {user_name}\n"
        f"🔑 **Key:** `{api_key_to_use}`\n"
        f"✅ **Status:** {status_text}\n\n"
        f"⚡ **Daily Remaining:** {daily_rem}\n"
        f"❤️ **Fix Count:** 100 likes per request\n\n"
        f"🕒 `{current_time_str}`"
    )

    await update.message.reply_text(msg, parse_mode='Markdown')

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_subscriptions or not active_subscriptions[user_id]:
        await update.message.reply_text("❌ আপনার কোনো সক্রিয় লাইক প্যাকেজ নেই। আগে `/add` দিয়ে প্যাকেজ যোগ করুন।", parse_mode='Markdown')
        return

    if not context.args:
        await update.message.reply_text("❌ সময় প্রদান করুন! ২৪ ঘণ্টার ফরম্যাটে দিন।\nউদাহরণ: `/time 18:27`", parse_mode='Markdown')
        return

    time_input = context.args[0].strip()
    try:
        parsed_time = datetime.strptime(time_input, "%H:%M").strftime("%H:%M")
    except ValueError:
        await update.message.reply_text("❌ ভুল সময়ের ফরম্যাট! উদাহরণ: `/time 18:27`", parse_mode='Markdown')
        return

    for sub in active_subscriptions[user_id]:
        sub["auto_time"] = parsed_time

    await update.message.reply_text(f"⏰ অটো লাইকের সময় সফলভাবে **{parsed_time}** নির্ধারণ করা হয়েছে।", parse_mode='Markdown')

async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/like [UID]`", parse_mode='Markdown')
        return

    user_id = update.effective_user.id
    api_key_to_use = user_api_keys.get(user_id, LIKE_API_KEY)
    uid = str(context.args[0]).strip()
    
    bd_now = datetime.utcnow() + timedelta(hours=6)
    current_time = bd_now.strftime("%I:%M %p, %d %b %Y")
    
    data, status = send_like_request(api_key_to_use, uid)

    if status == 200 and data:
        name = data.get("Name") or data.get("player_name") or data.get("name") or "N/A"
        likes_given = data.get("Likes Sent") or data.get("likes_given") or 100
        before = data.get("Before") or data.get("likes_before") or "N/A"
        after = data.get("After") or data.get("likes_after") or "N/A"
        daily_rem = data.get("Daily Remaining") or data.get("daily_remaining") or "N/A"

        if likes_given or str(data.get("status", "")).lower() == "success":
            msg = (
                "🔥 **MARUF LIKE BOT**\n\n"
                "✅ **Likes Sent Successfully!**\n\n"
                f"👤 **UID:** `{uid}`\n"
                f"📛 **Name:** `{name}`\n"
                f"❤️ **Likes Sent:** +{likes_given}\n"
                f"📊 **Before:** {before}\n"
                f"📈 **After:** {after}\n"
                f"⚡ **Daily Remaining:** {daily_rem}\n\n"
                f"🕒 `{current_time}`"
            )
        else:
            current_likes = data.get("Current Likes") or data.get("current_likes") or "N/A"
            reason = data.get("Reason") or data.get("message") or "No new likes added"

            msg = (
                "🔥 **MARUF LIKE BOT**\n\n"
                "⚠️ **No New Likes Added!**\n\n"
                f"🎯 **UID:** `{uid}`\n"
                f"📛 **Name:** `{name}`\n"
                f"📊 **Current Likes:** {current_likes}\n"
                f"❌ **Reason:** {reason}\n\n"
                f"🕒 `{current_time}`"
            )
    else:
        msg = f"❌ **API Error! Status Code: 404**\n\nসার্ভার লিংক পাওয়া যায়নি অথবা আপনার API Key বন্ধ। আপনার লাইক প্রোভাইডারের থেকে সঠিক Key ও URL লিংক সংগ্রহ করুন।"

    await update.message.reply_text(msg, parse_mode='Markdown')

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subs = active_subscriptions.get(user_id, [])
    if not subs:
        await update.message.reply_text("📋 কোনো সক্রিয় শেডিউল পাওয়া যায়নি।")
        return
    msg = "📋 **Active Schedules:**\n\n"
    for idx, sub in enumerate(subs, 1):
        msg += f"**{idx}. UID:** `{sub['uid']}` | **Auto Time:** `{sub['auto_time']}`\n"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ আপনি অ্যাডমিন নন!")
        return
    await update.message.reply_text("⚙️ **Admin Panel Active!**")

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)

async def main():
    global telegram_app
    telegram_app = Application.builder().token(BOT_TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(CommandHandler("help", help_command))
    telegram_app.add_handler(CommandHandler("key", key_command))
    telegram_app.add_handler(CommandHandler("support", support_command))
    telegram_app.add_handler(CommandHandler("number", number_command))
    telegram_app.add_handler(CommandHandler("rate", rate_command))
    telegram_app.add_handler(CommandHandler("balance", balance_command))
    telegram_app.add_handler(CommandHandler("verify", verify_command))
    telegram_app.add_handler(CommandHandler("add", add_command))
    telegram_app.add_handler(CommandHandler("delete", delete_command))
    telegram_app.add_handler(CommandHandler("usage", usage_command))
    telegram_app.add_handler(CommandHandler("time", time_command))
    
    telegram_app.add_handler(CommandHandler("like", like_command))
    telegram_app.add_handler(CommandHandler("Like", like_command))
    
    telegram_app.add_handler(CommandHandler("list", list_command))
    telegram_app.add_handler(CommandHandler("admin", admin_command))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))

    asyncio.create_task(auto_like_checker())

    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_flask)

    await telegram_app.initialize()
    await telegram_app.start()
    await set_bot_commands(telegram_app)
    
    print("Telegram Bot Started Successfully!")
    
    await telegram_app.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
    
