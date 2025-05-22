from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, MessageHandler, filters, ContextTypes
)
import asyncio
import nest_asyncio
from datetime import datetime
import re

# === Bot Tokens ===
TOKEN_1 = '7676608640:AAHvTxh5oDfWIz49au-iG_jexKZxnut805U'  # Bot 1 Token for Link Deletion
TOKEN_2 = '7182575750:AAGg3K8OkwKekYCeHf5Bv2lPZClZ8CwQnq0'  # Bot 2 Token for Replies and Welcomes

# === YOUR GROUP CHAT ID ===
GROUP_CHAT_ID = -1007081768586  # Supergroup ID (always negative)

# === Bot 1: Link Deletion (Non-admin link deletion) ===
async def handle_link_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    message = update.effective_message

    if any(entity.type in ['url', 'text_link'] for entity in message.entities or []):
        member = await context.bot.get_chat_member(chat_id, user_id)
        if member.status not in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]:
            await message.delete()
            print(f"[Link Deleted] From: {update.effective_user.first_name}")

# === Bot 2: Welcome and Reply ===
async def welcome_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        for new_member in update.message.new_chat_members:
            await update.message.reply_text(f"Welcome {new_member.first_name}! 🎉")

async def reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    user_name = update.message.from_user.first_name
    print(f"[Received] {user_name}: {text}")  # Debugging

    # Regex matching for flexible reply handling
    if re.search(r'\b(hi|hello|hey|sup|yo)\b', text):
        await update.message.reply_text(f"Hello {user_name}, you are welcome!")
    elif re.search(r"(what('?s| is) the time)", text):
        now = datetime.now().strftime('%I:%M %p')
        await update.message.reply_text(f"The time is {now}, {user_name}.")
    elif re.search(r'who are you', text):
        await update.message.reply_text(f"I'm ModuBot, your helpful group assistant, {user_name}!")

# === Main Bot Loop ===
async def run_bots():
    app1 = ApplicationBuilder().token(TOKEN_1).build()
    app2 = ApplicationBuilder().token(TOKEN_2).build()

    # Bot 1: Link deletion handler
    app1.add_handler(MessageHandler(filters.ALL, handle_link_deletion))

    # Bot 2: Welcome and reply handlers
    app2.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_member))
    app2.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), reply))

    print("Bots are running...")
    await asyncio.gather(
        app1.run_polling(),
        app2.run_polling()
    )

# === Run the bots ===
if __name__ == '__main__':
    nest_asyncio.apply()
    asyncio.get_event_loop().run_until_complete(run_bots())
