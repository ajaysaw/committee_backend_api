import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class CommitteeType(str, enum.Enum):
    LUCKY_DRAW = "lucky_draw"
    BIDDING = "bidding"
    PERCENTAGE = "percentage"


class CommitteeStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MembershipStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    LEFT = "left"
    REMOVED = "removed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    LATE = "late"
    MISSED = "missed"
    PARTIAL = "partial"


class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    CHEQUE = "cheque"
    ONLINE = "online"


class TransactionType(str, enum.Enum):
    CONTRIBUTION = "contribution"
    PAYOUT = "payout"
    DIVIDEND = "dividend"
    INTEREST = "interest"
    PENALTY = "penalty"
    REFUND = "refund"


class BidStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class RoundStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class NotificationType(str, enum.Enum):
    PAYMENT_REMINDER = "payment_reminder"
    PAYMENT_RECEIVED = "payment_received"
    BID_STARTED = "bid_started"
    BID_WON = "bid_won"
    LUCKY_DRAW_RESULT = "lucky_draw_result"
    COMMITTEE_JOINED = "committee_joined"
    COMMITTEE_STARTED = "committee_started"
    PAYOUT_PROCESSED = "payout_processed"
    GENERAL = "general"


class AuditAction(str, enum.Enum):
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    LOGIN = "login"
    LOGOUT = "logout"
    PAYMENT = "payment"
    PAYOUT = "payout"
    BID = "bid"
    DRAW = "draw"
