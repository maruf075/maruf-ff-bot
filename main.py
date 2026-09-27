# --- Render Port Detection Fix ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is active 24/7!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    web_app.run(host='0.0.0.0', port=port)

# --- Main Running Logic ---
def main():
    # Flask ওয়েব সার্ভার আলাদা থ্রেডে চালু
    server_thread = Thread(target=run_flask, daemon=True)
    server_thread.start()

    # Telegram Bot Application Setup
    telegram_app = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # Handlers Registration
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
    telegram_app.add_handler(CommandHandler("stock", stock_command))
    telegram_app.add_handler(CommandHandler("topup", topup_command))
    telegram_app.add_handler(CommandHandler("tp", topup_command))
    telegram_app.add_handler(CommandHandler("addvoucher", addvoucher_command))
    telegram_app.add_handler(CommandHandler("setrate", setrate_command))
    telegram_app.add_handler(CommandHandler("addbalance", addbalance_command))
    telegram_app.add_handler(CommandHandler("cutbalance", cutbalance_command))
    telegram_app.add_handler(CommandHandler("list", list_command))
    telegram_app.add_handler(CommandHandler("admin", admin_command))
    telegram_app.add_handler(CallbackQueryHandler(button_handler))

    # Polling Run
    telegram_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
    
