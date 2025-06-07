from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
import logging
import requests
import os
from datetime import datetime, timedelta

BOT_TOKEN = os.getenv("BOT_TOKEN")
PHANTOM_ADDRESS = os.getenv("PHANTOM_ADDR")
GROUP_CHAT_ID = os.getenv("CHAT_ID")  # -100xxxxxxxxxx formatında

WAITING_FOR_WALLET = 1

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

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

# Kullanıcının gönderdiği cüzdan adresine göre son işlemleri kontrol et
async def check_transaction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sender_address = update.message.text.strip()
    url = f"https://public-api.solscan.io/account/transactions?account={PHANTOM_ADDRESS}&limit=10"
    headers = {"accept": "application/json", "User-Agent": "Mozilla/5.0"}

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
                    await update.message.reply_text("✅ Ödemen onaylandı. Seni premium gruba ekliyorum...")
                    try:
                        await context.bot.add_chat_members(chat_id=int(GROUP_CHAT_ID), user_ids=[update.effective_user.id])
                        await update.message.reply_text("🎉 Premium gruba başarıyla eklendin!")
                    except Exception as e:
                        logging.error(f"Gruba ekleme hatası: {e}")
                        await update.message.reply_text("⚠️ Gruba ekleme sırasında bir hata oluştu. Lütfen yöneticiden yardım iste.")
                    return ConversationHandler.END

        await update.message.reply_text("❌ Henüz bu adresten 0.5 SOL gönderimi görünmüyor.")
        return ConversationHandler.END

    except Exception as e:
        logging.error(f"API hatası: {e}")
        await update.message.reply_text("⚠️ İşlem sırasında bir hata oluştu. Daha sonra tekrar deneyin.")
        return ConversationHandler.END

# Chat ID'yi gösteren komut
async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"✅ Bu grubun Chat ID'si: {update.effective_chat.id}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={WAITING_FOR_WALLET: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_transaction)]},
        fallbacks=[]
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('chatid', get_chat_id))
    app.run_polling()
