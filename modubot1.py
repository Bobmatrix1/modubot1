import os
import re
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes
)
import uvicorn

# === Environment Variables ===
TOKEN_1 = os.environ.get("TOKEN_1")  # Link deletion bot
TOKEN_2 = os.environ.get("TOKEN_2")  # Welcome & reply bot
WEBHOOK_URL_1 = os.environ.get("WEBHOOK_URL_1")  # /webhook1
WEBHOOK_URL_2 = os.environ.get("WEBHOOK_URL_2")  # /webhook2

# Safety checks
assert TOKEN_1 and TOKEN_2, "Both bot tokens must be set!"
assert WEBHOOK_URL_1 and WEBHOOK_URL_2, "Both webhook URLs must be set!"

# === FastAPI App ===
app = FastAPI()

bot1_app = None
bot2_app = None

# === Root route to prevent 404s ===
@app.get("/")
async def root():
    return {"message": "Bot is live and working!"}

# === Link Deletion Handler (Bot 1) ===
async def handle_link_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if message and any(entity.type in ['url', 'text_link'] for entity in message.entities or []):
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            await message.delete()
            print(f"[Link Deleted] From: {update.effective_user.first_name}")

# === Welcome New Member (Bot 2) ===
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    for new_member in update.message.new_chat_members:
        await update.message.reply_text(f"Welcome {new_member.first_name}! 🎉")

# === Auto Reply Handler (Bot 2) ===
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

# === Startup: Initialize bots and set webhooks ===
@app.on_event("startup")
async def startup_event():
    global bot1_app, bot2_app

    # Build applications
    bot1_app = ApplicationBuilder().token(TOKEN_1).build()
    bot2_app = ApplicationBuilder().token(TOKEN_2).build()

    # Add handlers
    bot1_app.add_handler(MessageHandler(filters.ALL, handle_link_deletion))
    bot2_app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    bot2_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, reply))

    # Initialize apps
    await bot1_app.initialize()
    await bot2_app.initialize()

    # Set webhooks
    await bot1_app.bot.set_webhook(WEBHOOK_URL_1)
    await bot2_app.bot.set_webhook(WEBHOOK_URL_2)

    print("[Startup] Bots initialized and webhooks set!")

# === Webhook Endpoints ===
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

# === Run App ===
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("modubot1:app", host="0.0.0.0", port=port)
