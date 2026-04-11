from sqlalchemy.orm import Session
from app.models.models import Transaction, User
from app.models.enums import UserRole


class TransactionService:

    @staticmethod
    def get_member_transactions(
        db: Session, user: User, committee_id: int = None,
        page: int = 1, page_size: int = 20,
    ) -> dict:
        query = db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.deleted_at == None,
        )
        if committee_id:
            query = query.filter(Transaction.committee_id == committee_id)

        total = query.count()
        txns = query.order_by(Transaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for t in txns:
            data.append({
                "id": t.id,
                "committee_id": t.committee_id,
                "transaction_type": t.transaction_type.value,
                "amount": str(t.amount),
                "balance_after": str(t.balance_after) if t.balance_after else None,
                "description": t.description,
                "round_number": t.round_number,
                "created_at": str(t.created_at),
            })

        return {
            "status": True,
            "message": "Transactions fetched",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }

    @staticmethod
    def get_committee_transactions(
        db: Session, committee_id: int, user: User,
        page: int = 1, page_size: int = 20,
    ) -> dict:
        query = db.query(Transaction).filter(
            Transaction.committee_id == committee_id,
            Transaction.deleted_at == None,
        )

        total = query.count()
        txns = query.order_by(Transaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()

        data = []
        for t in txns:
            user_obj = db.query(User).filter(User.id == t.user_id).first()
            data.append({
                "id": t.id,
                "user_id": t.user_id,
                "user_name": user_obj.name if user_obj else None,
                "transaction_type": t.transaction_type.value,
                "amount": str(t.amount),
                "description": t.description,
                "round_number": t.round_number,
                "created_at": str(t.created_at),
            })

        return {
            "status": True,
            "message": "Committee transactions",
            "data": data,
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
