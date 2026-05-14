import os
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_ID = int(os.getenv("GROUP_ID"))
OWNER_ID = int(os.getenv("OWNER_ID"))

banned_users = set()
users = set()

# START
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users.add(user.id)

    await update.message.reply_text(
        "👋 Hello!\n\nSend me any message and admin will reply soon."
    )

# USER MESSAGE → GROUP
async def user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if user.id in banned_users:
        return

    users.add(user.id)

    caption = f"""
📩 New Message

👤 Name: {user.first_name}
🆔 ID: {user.id}
📛 Username: @{user.username}

Reply to this message to answer user.
"""

    msg = update.message

    # TEXT
    if msg.text:
        sent = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=caption + f"\n💬 {msg.text}"
        )

    # PHOTO
    elif msg.photo:
        sent = await context.bot.send_photo(
            chat_id=GROUP_ID,
            photo=msg.photo[-1].file_id,
            caption=caption + f"\n🖼 Photo"
        )

    # VIDEO
    elif msg.video:
        sent = await context.bot.send_video(
            chat_id=GROUP_ID,
            video=msg.video.file_id,
            caption=caption + f"\n🎥 Video"
        )

    # DOCUMENT
    elif msg.document:
        sent = await context.bot.send_document(
            chat_id=GROUP_ID,
            document=msg.document.file_id,
            caption=caption + f"\n📁 File"
        )

    else:
        sent = await context.bot.send_message(
            chat_id=GROUP_ID,
            text=caption + "\n⚠ Unsupported message type"
        )

    context.bot_data[sent.message_id] = user.id

# ADMIN REPLY → USER
async def admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return

    if not update.message.reply_to_message:
        return

    original_msg_id = update.message.reply_to_message.message_id

    if original_msg_id not in context.bot_data:
        return

    user_id = context.bot_data[original_msg_id]

    try:
        if update.message.text:
            await context.bot.send_message(user_id, f"💬 Admin:\n\n{update.message.text}")

        elif update.message.photo:
            await context.bot.send_photo(
                user_id,
                update.message.photo[-1].file_id,
                caption=update.message.caption or ""
            )

        elif update.message.video:
            await context.bot.send_video(
                user_id,
                update.message.video.file_id,
                caption=update.message.caption or ""
            )

        elif update.message.document:
            await context.bot.send_document(
                user_id,
                update.message.document.file_id,
                caption=update.message.caption or ""
            )

    except:
        await update.message.reply_text("❌ Failed to send message.")

# BAN
async def ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        return await update.message.reply_text("/ban user_id")

    user_id = int(context.args[0])
    banned_users.add(user_id)

    await update.message.reply_text(f"🚫 Banned {user_id}")

# UNBAN
async def unban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    if len(context.args) != 1:
        return await update.message.reply_text("/unban user_id")

    user_id = int(context.args[0])

    banned_users.discard(user_id)

    await update.message.reply_text(f"✅ Unbanned {user_id}")

# USERS
async def users_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    await update.message.reply_text(f"👥 Total Users: {len(users)}")

# BROADCAST
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return

    text = " ".join(context.args)

    if not text:
        return await update.message.reply_text("/broadcast message")

    success = 0

    for user_id in users:
        try:
            await context.bot.send_message(user_id, text)
            success += 1
            await asyncio.sleep(0.05)
        except:
            pass

    await update.message.reply_text(f"✅ Sent to {success} users")

# MAIN
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ban", ban))
    app.add_handler(CommandHandler("unban", unban))
    app.add_handler(CommandHandler("users", users_count))
    app.add_handler(CommandHandler("broadcast", broadcast))

    app.add_handler(
        MessageHandler(
            filters.Chat(GROUP_ID) & filters.REPLY,
            admin_reply
        )
    )

    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            user_message
        )
    )

    print("Bot Running...")
    app.run_polling()

if __name__ == "__main__":
    main()
