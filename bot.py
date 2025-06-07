from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import logging
import requests
import os
from datetime import datetime, timedelta

# .env üzerinden token ve sabit değerleri al
BOT_TOKEN = os.getenv("BOT_TOKEN")
PREMIUM_LINK = os.getenv("PREMIUM_LINK")
PHANTOM_ADDRESS = os.getenv("PHANTOM_ADDR")

# Sabitler
WAITING_FOR_WALLET = 1

# Log ayarı
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = (
        f"👋 Hoş geldin {user.first_name}!\n\n"
        f"Açık Pozisyon Premium'a katılmak için 0.5 SOL ödeme kontrolü yapacağız.\n"
        f"Lütfen ödemenin gönderildiği cüzdan adresini (SENDER) buraya yaz."
    )
    await update.message.reply_text(message)
    return WAITING_FOR_WALLET

# Kullanıcıdan cüzdan adresi al ve kontrol et
async def check_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_address = update.message.text.strip()
    url = f"https://public-api.solscan.io/account/transactions?account={PHANTOM_ADDRESS}&limit=10"

    headers = {
        "accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        now = datetime.utcnow()

        for tx in data:
            if not tx.get("parsedInstruction"):
                continue

            for instruction in tx["parsedInstruction"]:
                source = instruction.get("source")
                lamports = int(instruction.get("lamport", 0))
                time_str = tx.get("blockTime")
                if not (source and lamports and time_str):
                    continue

                dt = datetime.utcfromtimestamp(time_str)
                if source == sender_address and lamports >= 500_000_000 and now - dt < timedelta(minutes=15):
                    await update.message.reply_text(
                        f"✅ Ödeme alındı! Premium gruba katılmak için link:\n{PREMIUM_LINK}"
                    )
                    return ConversationHandler.END

        await update.message.reply_text("❌ Henüz bu adresten 0.5 SOL gönderimi görünmüyor. Lütfen kontrol edip tekrar deneyin.")
        return ConversationHandler.END

    except Exception as e:
        logging.error(f"Hata: {e}")
        await update.message.reply_text("⚠️ İşlem sırasında bir hata oluştu. Daha sonra tekrar deneyin.")
        return ConversationHandler.END

# Botu başlat
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAITING_FOR_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_transaction)]
        },
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.run_polling()
