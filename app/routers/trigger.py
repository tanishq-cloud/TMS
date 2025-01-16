from fastapi import APIRouter, Depends
from app import models
from app.utils.auth import get_current_user
from app.utils.scheduler import notify_due_tasks

router = APIRouter()

@router.get("/notify")
async def tiggerNotification(
    current_user: models.User = Depends(get_current_user)):
    await notify_due_tasks()
    return {"message": "Notification sent - Check Telegram bot and Mail."}
    


