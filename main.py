import os
import asyncio
import requests
from datetime import datetime, timedelta
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# --- আপনার টোকেন ও এপিআই তথ্য ---
BOT_TOKEN = "8915748936:AAGPXAt0h-7tWOPpumGWrzoYejXf3xRPHJQ"
LIKE_API_KEY = "VALT2H"

ADMIN_IDS = [6347427263, 6992868111]  
TELEGRAM_SUPPORT_USERNAME = "@maruf3900"  
WHATSAPP_NUMBER = "+8801618203922"              

user_balances = {}
active_subscriptions = {}

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is Live and Running 24/7!"

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

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📜 **বটের সকল কমান্ডের তালিকা:**\n\n"
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
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/delete [Schedule_ID]`\nআপনার শেডিউল আইডি দেখতে `/list` টাইপ করুন।", parse_mode='Markdown')
        return

    sub_id_to_delete = context.args[0].upper().strip()
    user_subs = active_subscriptions.get(user_id, [])

    for sub in user_subs:
        if sub["sub_id"] == sub_id_to_delete:
            user_subs.remove(sub)
            await update.message.reply_text(f"🗑️ সফলভাবে Schedule ID `{sub_id_to_delete}` (UID: `{sub['uid']}`) ডিলিট করা হয়েছে!", parse_mode='Markdown')
            return

    await update.message.reply_text(f"❌ Schedule ID `{sub_id_to_delete}` খুঁজে পাওয়া যায়নি! আপনার সঠিক ID দেখতে `/list` লিখুন।", parse_mode='Markdown')

async def usage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_time = datetime.now().strftime("%I:%M %p, %d %b %Y")
    api_url = f"https://api.freefirelike.com/details?key={LIKE_API_KEY}"

    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()

            username = data.get("username", "Maruf")
            status = data.get("status", "Active")
            created = data.get("created", "N/A")
            expires = data.get("expires", "N/A")
            expiry_days = data.get("expiry_days", "N/A")

            daily_usage = data.get("daily_usage", "N/A")
            daily_remaining = data.get("daily_remaining", "N/A")
            monthly_usage = data.get("monthly_usage", "N/A")
            monthly_remaining = data.get("monthly_remaining", "N/A")

            total_usage = data.get("total_usage", 0)
            today_usage = data.get("today_usage", 0)
            this_month = data.get("this_month", 0)

            msg = (
                "🔑 **API Key Usage Details**\n\n"
                f"👤 **Username:** {username}\n"
                f"🔑 **Key:** `{LIKE_API_KEY}`\n"
                f"✅ **Status:** 🟢 {status}\n"
                f"📅 **Created:** {created}\n"
                f"⏰ **Expires:** {expires}\n"
                f"⚠️ **Expiry Status:** Expires in {expiry_days}\n\n"
                f"📊 **Daily Usage:** {daily_usage}\n"
                f"⚡ **Daily Remaining:** {daily_remaining}\n\n"
                f"📅 **Monthly Usage:** {monthly_usage}\n"
                f"⚡ **Monthly Remaining:** {monthly_remaining}\n\n"
                "❤️ **Fix Count:** 100 likes per request\n"
                f"📊 **Total Usage:** {total_usage}\n\n"
                "📈 **Usage Statistics:**\n"
                f"• **Today:** {today_usage}\n"
                f"• **This Month:** {this_month}\n"
                f"• **All Time:** {total_usage}\n\n"
                f"🕒 `{current_time}`"
            )
        else:
            raise Exception("API Error")
    except Exception:
        msg = (
            "🔑 **API Key Usage Details**\n\n"
            "👤 **Username:** Maruf\n"
            f"🔑 **Key:** `{LIKE_API_KEY}`\n"
            "✅ **Status:** 🟢 Active\n\n"
            f"🕒 `{current_time}`"
        )

    await update.message.reply_text(msg, parse_mode='Markdown')

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    subs = active_subscriptions.get(user_id, [])

    if not subs:
        await update.message.reply_text("📋 **Active Schedules:**\n\nকোনো সক্রিয় শেডিউল পাওয়া যায়নি।", parse_mode='Markdown')
        return

    msg = "📋 **Active Schedules:**\n\n"
    for idx, sub in enumerate(subs, 1):
        now = datetime.now()
        rem_days = max(0, (sub["end_date"] - now).days)
        ends_str = sub["end_date"].strftime("%d %b %Y")

        msg += (
            f"**{idx}. UID:** `{sub['uid']}`\n"
            f"   ⏱ **Duration:** {sub['total_days']} days\n"
            f"   📅 **Ends:** {ends_str}\n"
            f"   ⏳ **Remaining:** {rem_days} days\n"
            f"   ✅ **Total Sent:** {sub['used_likes']}\n"
            f"   🆔 **ID:** `{sub['sub_id']}`\n\n"
        )

    msg += f"📄 **Showing 1–{len(subs)} of {len(subs)}**"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_subscriptions or not active_subscriptions[user_id]:
        await update.message.reply_text("❌ আপনার কোনো সক্রিয় লাইক প্যাকেজ নেই।")
        return

    if not context.args:
        await update.message.reply_text("❌ সময় প্রদান করুন।\nউদাহরণ: `/time 14:30` (২৪ ঘণ্টার ফরম্যাটে)", parse_mode='Markdown')
        return

    set_time = context.args[0]
    for sub in active_subscriptions[user_id]:
        sub["auto_time"] = set_time
    await update.message.reply_text(f"⏰ অটো লাইকের সময় সফলভাবে **{set_time}** টায় নির্ধারণ করা হয়েছে।", parse_mode='Markdown')

# --- /like রিকোয়েস্ট (উন্নত ও ফিক্সড ভার্সন) ---
async def like_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ ভুল ফরম্যাট! সঠিক নিয়ম: `/like [UID]`\nউদাহরণ: `/like 12345678`", parse_mode='Markdown')
        return

    uid = str(context.args[0]).strip()
    current_time = datetime.now().strftime("%I:%M %p, %d %b %Y")
    
    # আসল API এন্ডপয়েন্ট
    api_url = f"https://api.freefirelike.com/like?key={LIKE_API_KEY}&uid={uid}"

    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            
            # নাম খুঁজে বের করার মাল্টিপল ফিল্ড সিস্টেম
            name = (
                data.get("Name") or 
                data.get("player_name") or 
                data.get("name") or 
                data.get("nickname") or 
                data.get("Player") or
                "N/A"
            )

            # লাইক সাকসেস চেক
            likes_given = data.get("Likes Sent") or data.get("likes_given") or data.get("likes_sent")
            before = data.get("Before") or data.get("likes_before") or data.get("before") or "N/A"
            after = data.get("After") or data.get("likes_after") or data.get("after") or "N/A"
            daily_rem = data.get("Daily Remaining") or data.get("daily_remaining") or "N/A"

            if likes_given or str(data.get("status", "")).lower() == "success":
                likes_sent = likes_given if likes_given else 100
                msg = (
                    "🔥 **MARUF LIKE BOT**\n\n"
                    "✅ **Likes Sent Successfully!**\n\n"
                    f"👤 **UID:** `{uid}`\n"
                    f"📛 **Name:** `{name}`\n"
                    f"❤️ **Likes Sent:** +{likes_sent}\n"
                    f"📊 **Before:** {before}\n"
                    f"📈 **After:** {after}\n"
                    f"⚡ **Daily Remaining:** {daily_rem}\n\n"
                    f"🕒 `{current_time}`"
                )
            else:
                # যদি লাইক না যায় (যেমন গেম লিমিট শেষ হয়ে থাকলে)
                current_likes = data.get("Current Likes") or data.get("current_likes") or "N/A"
                reason = data.get("Reason") or data.get("message") or "No new likes were added."

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
            msg = f"❌ **API Error!** Status Code: {response.status_code}"

    except Exception as e:
        msg = f"❌ **Connection Error:** {str(e)}"

    await update.message.reply_text(msg, parse_mode='Markdown')

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

async def main():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("support", support_command))
    application.add_handler(CommandHandler("number", number_command))
    application.add_handler(CommandHandler("rate", rate_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("verify", verify_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("delete", delete_command))
    application.add_handler(CommandHandler("usage", usage_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("time", time_command))
    application.add_handler(CommandHandler("like", like_command))

    application.add_handler(CommandHandler("admin", admin_help))
    application.add_handler(CommandHandler("addbalance", admin_add_balance))

    application.add_handler(CallbackQueryHandler(button_handler))

    port = int(os.environ.get("PORT", 10000))
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, lambda: app.run(host='0.0.0.0', port=port, use_reloader=False))

    await application.initialize()
    await application.start()
    await set_bot_commands(application)
    
    print("Telegram Bot Started Successfully!")
    
    await application.updater.start_polling(drop_pending_updates=True)
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
        
