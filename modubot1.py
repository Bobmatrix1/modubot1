import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes
)
from datetime import datetime
import re

# === Bot Tokens (set these in Render Environment Variables) ===
TOKEN_1 = os.environ.get("7676608640:AAHvTxh5oDfWIz49au-iG_jexKZxnut805U")  # Link deletion bot
TOKEN_2 = os.environ.get("7182575750:AAGg3K8OkwKekYCeHf5Bv2lPZClZ8CwQnq0")  # Welcome + Chat responder

# === Webhook URLs (set these in Render Environment Variables) ===
WEBHOOK_URL_1 = os.environ.get("https://modubot1-2.onrender.com/webhook1")
WEBHOOK_URL_2 = os.environ.get("https://modubot1-2.onrender.com/webhook2")

app = FastAPI()

# === Bot 1: Handle Link Deletion ===
async def handle_link_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        message = update.effective_message
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        print(f"[DEBUG] Message received: {message.text}")
        print(f"[DEBUG] Entities: {message.entities}")

        entities = message.entities or []
        if any(entity.type in ['url', 'text_link'] for entity in entities):
            member = await context.bot.get_chat_member(chat_id, user_id)
            print(f"[DEBUG] Member status: {member.status}")

            if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
                await message.delete()
                print(f"[Link Deleted] From: {update.effective_user.first_name}")
    except Exception as e:
        print(f"[ERROR] Link deletion failed: {e}")

# === Bot 2: Handle Welcome Message ===
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        await update.message.reply_text(f"Welcome {new_member.first_name}! 🎉")

# === Bot 2: Handle Replies ===
async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_name = update.message.from_user.first_name

    if re.search(r'\b(hi|hello|hey|sup|yo)\b', text):
        await update.message.reply_text(f"Hello {user_name}, you are welcome!")
    elif re.search(r"(what('?s| is) the time)", text):
        now = datetime.now().strftime('%I:%M %p')
        await update.message.reply_text(f"The time is {now}, {user_name}.")
    elif re.search(r'who are you', text):
        await update.message.reply_text(f"I'm ModuBot, your helpful group assistant, {user_name}!")

# === Set up bots ===
bot1_app = None
bot2_app = None

@app.on_event("startup")
async def startup_event():
    global bot1_app, bot2_app

    bot1_app = ApplicationBuilder().token(TOKEN_1).build()
    bot2_app = ApplicationBuilder().token(TOKEN_2).build()

    # Bot 1: Only handle messages containing links (url or text_link)
    link_filter = filters.TEXT & (filters.Entity("url") | filters.Entity("text_link"))
    bot1_app.add_handler(MessageHandler(link_filter, handle_link_deletion))

    # Bot 2: Welcome and text reply
    bot2_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    bot2_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # Set webhook URLs
    await bot1_app.bot.set_webhook(WEBHOOK_URL_1)
    await bot2_app.bot.set_webhook(WEBHOOK_URL_2)

# === Webhook endpoints for Telegram ===
@app.post("/webhook1")
async def webhook1(request: Request):
    if bot1_app is None:
        raise HTTPException(status_code=503, detail="Bot 1 not initialized")
    update_data = await request.json()
    update = Update.de_json(update_data, bot1_app.bot)
    await bot1_app.process_update(update)
    return {"status": "ok"}

@app.post("/webhook2")
async def webhook2(request: Request):
    if bot2_app is None:
        raise HTTPException(status_code=503, detail="Bot 2 not initialized")
    update_data = await request.json()
    update = Update.de_json(update_data, bot2_app.bot)
    await bot2_app.process_update(update)
    return {"status": "ok"}
