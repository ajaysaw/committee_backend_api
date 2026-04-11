from sqlalchemy.orm import Session

from app.models.models import Notification, User


class NotificationService:

    @staticmethod
    def get_notifications(db: Session, user: User, page: int = 1, page_size: int = 20) -> dict:
        query = (
            db.query(Notification)
            .filter(Notification.user_id == user.id, Notification.deleted_at == None)
            .order_by(Notification.created_at.desc())
        )

        total = query.count()
        unread = (
            db.query(Notification)
            .filter(
                Notification.user_id == user.id,
                Notification.is_read == False,
                Notification.deleted_at == None,
            )
            .count()
        )

        notifications = query.offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for n in notifications:
            data.append({
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "notification_type": n.notification_type.value,
                "is_read": n.is_read,
                "reference_id": n.reference_id,
                "reference_type": n.reference_type,
                "created_at": str(n.created_at),
            })

        return {
            "status": True,
            "message": "Notifications fetched",
            "data": data,
            "total": total,
            "unread_count": unread,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def mark_read(db: Session, user: User, notification_ids: list[int]) -> dict:
        db.query(Notification).filter(
            Notification.id.in_(notification_ids),
            Notification.user_id == user.id,
        ).update({"is_read": True}, synchronize_session=False)

        db.commit()

        return {"status": True, "message": "Notifications marked as read"}

    @staticmethod
    def mark_all_read(db: Session, user: User) -> dict:
        db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.is_read == False,
        ).update({"is_read": True}, synchronize_session=False)

        db.commit()

        return {"status": True, "message": "All notifications marked as read"}
