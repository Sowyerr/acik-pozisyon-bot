from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import logging

# Token ve bilgiler
BOT_TOKEN = "7870474639:AAGpDbXF31Rf5BYzaRbMOBCfaDmjWXHAyDs"
PREMIUM_LINK = "https://t.me/+QWbBymtP3ns3M2I0"
PHANTOM_ADDRESS = "BKDQrhZAfXt6jSUv2M6JSRQam2486KXwa5H12HZfSeEe"

# Durum sabiti
WAITING_FOR_CONFIRM = 1

# Log ayarları
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    welcome_message = (
        f"👋 Hoş geldin {user.first_name}!\n\n"
        f"📈 Açık Pozisyon'a katılmak için 0.5 SOL gönder:\n"
        f"💳 `{PHANTOM_ADDRESS}`\n\n"
        f"✅ Gönderim yaptıysan aşağıdaki butona tıkla."
    )
    reply_markup = ReplyKeyboardMarkup([
        ["✅ Ödeme Yaptım"]
    ], one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")
    return WAITING_FOR_CONFIRM

# Ödeme onayı
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"✅ Ödemen onaylandıysa aşağıdaki linkten premium gruba katılabilirsin:\n\n"
        f"{PREMIUM_LINK}"
    )
    return ConversationHandler.END

# Botu başlat
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_CONFIRM: [
                MessageHandler(filters.Regex("^✅ Ödeme Yaptım$"), confirm_payment)
            ]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()
