from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.enums import NotificationType


class NotificationResponse(BaseModel):
    id: int
    title: str
    message: str
    notification_type: NotificationType
    is_read: bool
    reference_id: Optional[int] = None
    reference_type: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MarkReadRequest(BaseModel):
    notification_ids: list[int]
