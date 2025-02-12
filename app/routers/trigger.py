from fastapi import APIRouter, Depends, HTTPException
from app import models
from app.utils.auth import get_current_user
from app.utils.scheduler import notify_due_tasks

router = APIRouter()

@router.get("/notify")
async def tiggerNotification(
    current_user: models.User = Depends(get_current_user)):
    """It trigger notification, to notify the admin about the overdue task."""
    
    try:
        await notify_due_tasks()
        return {"message": "Notification sent - Check Telegram bot and Mail."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending notification: {str(e)}"
                            ) from e
