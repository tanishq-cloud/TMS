from telegram import Update
from telegram.ext import CommandHandler, ApplicationBuilder, ContextTypes
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app import models
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT')

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /start command.
    """
    await update.message.reply_text("Welcome! Use /subscribe to get task notifications.")

async def subscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /subscribe command and store user info in the database.
    """
    db = await anext(get_db())  # Get a database session instance
    try:
        chat_id = update.effective_chat.id
        username = update.effective_user.username
        first_name = update.effective_user.first_name
        last_name = update.effective_user.last_name

        # Check if the user is already subscribed
        result = await db.execute(
            select(models.TelegramSubscriber).where(models.TelegramSubscriber.chat_id == str(chat_id))
        )
        existing_user = result.scalar()

        if existing_user:
            await update.message.reply_text("You're already subscribed!")
        else:
            # Add new subscriber
            new_subscriber = models.TelegramSubscriber(
                chat_id=str(chat_id),
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            db.add(new_subscriber)
            await db.commit()
            await update.message.reply_text("Subscription successful! You will now receive notifications.")
    except Exception as e:
        print(f"Error in subscribe: {e}")
    finally:
        await db.close()  # Ensure the session is closed

async def unsubscribe(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle the /unsubscribe command and remove user info from the database.
    """
    db = await anext(get_db())  # Get a database session instance
    try:
        chat_id = update.effective_chat.id

        # Remove subscriber
        await db.execute(
            select(models.TelegramSubscriber).where(models.TelegramSubscriber.chat_id == str(chat_id)).delete()
        )
        await db.commit()

        await update.message.reply_text("You have unsubscribed successfully!")
    except Exception as e:
        print(f"Error in unsubscribe: {e}")
    finally:
        await db.close()  # Ensure the session is closed


async def send_message(chat_id, message):
    """
    Sends a message to a specific Telegram user.
    """
    try:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        await application.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
    except Exception as e:
        print(f"Failed to send message to {chat_id}: {e}")

def runBot():
    """
    Run the Telegram bot in polling mode.
    """
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("subscribe", subscribe))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe))

    # Start the bot
    print("Telegram bot is running...")
    application.run_polling()

if __name__ == "__main__":
    runBot()
