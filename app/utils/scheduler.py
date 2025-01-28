from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app import models
import asyncio
import logging
from telegram_BOT_Runner import send_message
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
import os


async def notify_due_tasks():
    try:
        
        db = await anext(get_db())

        
        now = datetime.now()
        deadline = now + timedelta(hours=24)

        result = await db.execute(
            select(models.Task).where(models.Task.due_date <=
                                      deadline, models.Task.status != "completed")
        )
        # tasks = result.scalars().all()

        if tasks := result.scalars().all():
            message = "⏰ *Upcoming Tasks Due in the Next 24 Hours:*\n\n"
            mailmessage = """
<h1>⏰ Upcoming Tasks Due in the Next 24 Hours:</h1>
<ul>"""
            for task in tasks:
                message += (
                    f"📌 *Task ID*: {task.task_id}\n"
                    f"📝 *Name*: {task.name}\n"
                    f"🔑 *Priority*: {task.priority}\n"
                    f"👤 *Assigned To*: {task.assigned_to}\n"
                    f"🗓 *Due Date*: {task.due_date.strftime(
                        '%Y-%m-%d %H:%M:%S')}\n"
                    f"💡 *Description*: {task.description or 'No description provided'}\n\n"
                )

                mailmessage += f"""
    <li>
        <strong>📌 Task ID:</strong> {task.task_id}<br>
        <strong>📝 Name:</strong> {task.name}<br>
        <strong>🔑 Priority:</strong> {task.priority}<br>
        <strong>👤 Assigned To:</strong> {task.assigned_to}<br>
        <strong>🗓 Due Date:</strong> {task.due_date.strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>💡 Description:</strong> {task.description or 'No description provided'}
    </li>
    <br>
    """
            mailmessage += "</ul>"

            
            result = await db.execute(select(models.TelegramSubscriber))
            subscribers = result.scalars().all()

            for subscriber in subscribers:
                try:
                    await send_message(chat_id=subscriber.chat_id, message=message)
                except Exception as e:
                    logging.error(f"Failed to send Telegram message to {
                                  subscriber.chat_id}: {e}")

            
            sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))

            mail_message = Mail(
                from_email='tanishqkumar@protonmail.com',
                to_emails='tanishqkumar@duck.com',
                subject='⏰ Upcoming Tasks Due in the Next 24 Hours',
                html_content=mailmessage
            )
            try:
                sg.send(mail_message)
            except Exception as e:
                logging.error(f"Failed to send email: {e}")
    except Exception as e:
        logging.error(f"Error in notify_due_tasks: {e}")


def init_scheduler():
    scheduler = AsyncIOScheduler()

    
    scheduler.add_job(notify_due_tasks, "interval", hours=12)
    return scheduler
