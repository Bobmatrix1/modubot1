import os
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes
)
from datetime import datetime
import re

# === Bot Tokens ===
TOKEN_1 = os.environ.get("TOKEN_1")  # Set this in Render env vars
TOKEN_2 = os.environ.get("TOKEN_2")  # Set this in Render env vars

# === Webhook URLs (Render URL + /webhook1 or /webhook2) ===
WEBHOOK_URL_1 = os.environ.get("WEBHOOK_URL_1")  # Set this too
WEBHOOK_URL_2 = os.environ.get("WEBHOOK_URL_2")

app = FastAPI()

# === Bot 1: Link Deletion Handler ===
async def handle_link_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if any(entity.type in ['url', 'text_link'] for entity in message.entities or []):
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            await message.delete()
            print(f"[Link Deleted] From: {update.effective_user.first_name}")

# === Bot 2: Welcome and Reply Handlers ===
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        await update.message.reply_text(f"Welcome {new_member.first_name}! 🎉")

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

# === Set up bot applications globally ===
bot1_app = None
bot2_app = None

@app.on_event("startup")
async def startup_event():
    global bot1_app, bot2_app

    bot1_app = ApplicationBuilder().token(TOKEN_1).build()
    bot2_app = ApplicationBuilder().token(TOKEN_2).build()

    bot1_app.add_handler(MessageHandler(filters.ALL, handle_link_deletion))
    bot2_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    bot2_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # Set webhook URLs for Telegram to send updates to
    await bot1_app.bot.set_webhook(WEBHOOK_URL_1)
    await bot2_app.bot.set_webhook(WEBHOOK_URL_2)

@app.post("/webhook1")
async def webhook1(request: Request):
    if bot1_app is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    update_data = await request.json()
    update = Update.de_json(update_data, bot1_app.bot)
    await bot1_app.process_update(update)
    return {"status": "ok"}

@app.post("/webhook2")
async def webhook2(request: Request):
    if bot2_app is None:
        raise HTTPException(status_code=503, detail="Bot not initialized")
    update_data = await request.json()
    update = Update.de_json(update_data, bot2_app.bot)
    await bot2_app.process_update(update)
    return {"status": "ok"}
