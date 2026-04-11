from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean, Float,
    Numeric, Date, DateTime, ForeignKey, Index, UniqueConstraint, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.database.connection import Base
from app.models.base import TimestampMixin
from app.models.enums import (
    UserRole, UserStatus, CommitteeType, CommitteeStatus,
    MembershipStatus, PaymentStatus, PaymentMethod,
    TransactionType, BidStatus, RoundStatus,
    NotificationType, AuditAction,
)


# ── 1. Users ──────────────────────────────────────────────
class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.MEMBER, nullable=False)
    status = Column(SAEnum(UserStatus), default=UserStatus.PENDING, nullable=False)
    avatar_url = Column(String(500), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    pincode = Column(String(10), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    sessions = relationship("UserSession", back_populates="user")
    memberships = relationship("CommitteeMember", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")
    notifications = relationship("Notification", back_populates="user")
    bids = relationship("Bid", back_populates="user")
    audit_logs = relationship("AuditLog", back_populates="user")


# ── 2. User Profiles ─────────────────────────────────────
class UserProfile(Base, TimestampMixin):
    __tablename__ = "user_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    date_of_birth = Column(Date, nullable=True)
    gender = Column(String(20), nullable=True)
    occupation = Column(String(255), nullable=True)
    aadhar_number = Column(String(20), nullable=True)
    pan_number = Column(String(20), nullable=True)
    bank_name = Column(String(255), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    bank_ifsc = Column(String(20), nullable=True)
    upi_id = Column(String(100), nullable=True)
    emergency_contact_name = Column(String(255), nullable=True)
    emergency_contact_phone = Column(String(20), nullable=True)

    user = relationship("User", back_populates="profile")


# ── 3. User Sessions ─────────────────────────────────────
class UserSession(Base, TimestampMixin):
    __tablename__ = "user_sessions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), nullable=False, index=True)
    refresh_token = Column(String(500), nullable=True)
    device_info = Column(String(500), nullable=True)
    ip_address = Column(String(45), nullable=True)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    user = relationship("User", back_populates="sessions")


# ── 4. OTP Verifications ─────────────────────────────────
class OTPVerification(Base, TimestampMixin):
    __tablename__ = "otp_verifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    otp_code = Column(String(10), nullable=False)
    otp_type = Column(String(50), nullable=False)  # registration, login, password_reset
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False)
    attempts = Column(Integer, default=0, nullable=False)


# ── 5. Committees ─────────────────────────────────────────
class Committee(Base, TimestampMixin):
    __tablename__ = "committees"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    committee_type = Column(SAEnum(CommitteeType), nullable=False)
    status = Column(SAEnum(CommitteeStatus), default=CommitteeStatus.DRAFT, nullable=False)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    total_members = Column(Integer, nullable=False)
    monthly_contribution = Column(Numeric(12, 2), nullable=False)
    total_amount = Column(Numeric(14, 2), nullable=False)
    duration_months = Column(Integer, nullable=False)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    current_round = Column(Integer, default=0, nullable=False)
    interest_rate = Column(Numeric(5, 2), default=0, nullable=True)
    min_bid_amount = Column(Numeric(12, 2), nullable=True)
    max_bid_amount = Column(Numeric(12, 2), nullable=True)
    rules = Column(Text, nullable=True)

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    members = relationship("CommitteeMember", back_populates="committee")
    rounds = relationship("CommitteeRound", back_populates="committee")
    payments = relationship("Payment", back_populates="committee")
    transactions = relationship("Transaction", back_populates="committee")
    settings_rel = relationship("CommitteeSetting", back_populates="committee")
    schedules = relationship("PaymentSchedule", back_populates="committee")

    __table_args__ = (
        Index("idx_committee_type", "committee_type"),
        Index("idx_committee_status", "status"),
    )


# ── 6. Committee Settings ────────────────────────────────
class CommitteeSetting(Base, TimestampMixin):
    __tablename__ = "committee_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    setting_key = Column(String(100), nullable=False)
    setting_value = Column(Text, nullable=False)

    committee = relationship("Committee", back_populates="settings_rel")

    __table_args__ = (
        UniqueConstraint("committee_id", "setting_key", name="uq_committee_setting"),
    )


# ── 7. Committee Members ─────────────────────────────────
class CommitteeMember(Base, TimestampMixin):
    __tablename__ = "committee_members"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    slot_number = Column(Integer, nullable=True)
    membership_status = Column(SAEnum(MembershipStatus), default=MembershipStatus.PENDING, nullable=False)
    has_received_payout = Column(Boolean, default=False, nullable=False)
    payout_round = Column(Integer, nullable=True)
    total_paid = Column(Numeric(14, 2), default=0, nullable=False)
    total_received = Column(Numeric(14, 2), default=0, nullable=False)
    joined_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="memberships")
    committee = relationship("Committee", back_populates="members")

    __table_args__ = (
        UniqueConstraint("committee_id", "user_id", name="uq_committee_user"),
        Index("idx_member_status", "membership_status"),
    )


# ── 8. Committee Rounds ──────────────────────────────────
class CommitteeRound(Base, TimestampMixin):
    __tablename__ = "committee_rounds"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    status = Column(SAEnum(RoundStatus), default=RoundStatus.PENDING, nullable=False)
    scheduled_date = Column(Date, nullable=True)
    completed_date = Column(Date, nullable=True)
    pool_amount = Column(Numeric(14, 2), default=0, nullable=False)
    winner_member_id = Column(BigInteger, ForeignKey("committee_members.id"), nullable=True)
    winner_amount = Column(Numeric(14, 2), nullable=True)
    discount_amount = Column(Numeric(12, 2), default=0, nullable=True)

    committee = relationship("Committee", back_populates="rounds")
    winner = relationship("CommitteeMember", foreign_keys=[winner_member_id])
    bids = relationship("Bid", back_populates="round")
    lucky_draw = relationship("LuckyDraw", back_populates="round", uselist=False)
    dividends = relationship("Dividend", back_populates="round")

    __table_args__ = (
        UniqueConstraint("committee_id", "round_number", name="uq_committee_round"),
    )


# ── 9. Bids ──────────────────────────────────────────────
class Bid(Base, TimestampMixin):
    __tablename__ = "bids"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    round_id = Column(BigInteger, ForeignKey("committee_rounds.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    bid_amount = Column(Numeric(12, 2), nullable=False)
    is_winner = Column(Boolean, default=False, nullable=False)

    round = relationship("CommitteeRound", back_populates="bids")
    user = relationship("User", back_populates="bids")
    committee = relationship("Committee")

    __table_args__ = (
        Index("idx_bid_round", "round_id"),
    )


# ── 10. Bid Settings ─────────────────────────────────────
class BidSetting(Base, TimestampMixin):
    __tablename__ = "bid_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), unique=True, nullable=False)
    min_bid_percentage = Column(Numeric(5, 2), default=0, nullable=False)
    max_bid_percentage = Column(Numeric(5, 2), default=100, nullable=False)
    bid_increment = Column(Numeric(10, 2), default=100, nullable=False)
    auto_close_minutes = Column(Integer, default=30, nullable=False)


# ── 11. Lucky Draws ──────────────────────────────────────
class LuckyDraw(Base, TimestampMixin):
    __tablename__ = "lucky_draws"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    round_id = Column(BigInteger, ForeignKey("committee_rounds.id", ondelete="CASCADE"), unique=True, nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    winner_member_id = Column(BigInteger, ForeignKey("committee_members.id"), nullable=True)
    draw_seed = Column(String(255), nullable=True)
    draw_timestamp = Column(DateTime, nullable=True)
    eligible_member_ids = Column(Text, nullable=True)  # JSON array of eligible member IDs

    round = relationship("CommitteeRound", back_populates="lucky_draw")
    winner = relationship("CommitteeMember")


# ── 12. Lucky Draw History ───────────────────────────────
class LuckyDrawHistory(Base, TimestampMixin):
    __tablename__ = "lucky_draw_history"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    lucky_draw_id = Column(BigInteger, ForeignKey("lucky_draws.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(BigInteger, ForeignKey("committee_members.id"), nullable=False)
    was_eligible = Column(Boolean, default=True, nullable=False)
    was_winner = Column(Boolean, default=False, nullable=False)


# ── 13. Payments ─────────────────────────────────────────
class Payment(Base, TimestampMixin):
    __tablename__ = "payments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    payment_status = Column(SAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), nullable=True)
    payment_date = Column(DateTime, nullable=True)
    due_date = Column(Date, nullable=False)
    late_fee = Column(Numeric(10, 2), default=0, nullable=False)
    reference_number = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="payments")
    committee = relationship("Committee", back_populates="payments")

    __table_args__ = (
        Index("idx_payment_status", "payment_status"),
        Index("idx_payment_user_committee", "user_id", "committee_id"),
    )


# ── 14. Payment Schedule ─────────────────────────────────
class PaymentSchedule(Base, TimestampMixin):
    __tablename__ = "payment_schedules"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    due_date = Column(Date, nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    committee = relationship("Committee", back_populates="schedules")

    __table_args__ = (
        UniqueConstraint("committee_id", "round_number", name="uq_schedule_round"),
    )


# ── 15. Transactions ─────────────────────────────────────
class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    transaction_type = Column(SAEnum(TransactionType), nullable=False)
    amount = Column(Numeric(14, 2), nullable=False)
    balance_after = Column(Numeric(14, 2), nullable=True)
    description = Column(Text, nullable=True)
    reference_id = Column(String(100), nullable=True)
    round_number = Column(Integer, nullable=True)

    user = relationship("User", back_populates="transactions")
    committee = relationship("Committee", back_populates="transactions")

    __table_args__ = (
        Index("idx_transaction_type", "transaction_type"),
        Index("idx_transaction_user", "user_id"),
    )


# ── 16. Dividends ────────────────────────────────────────
class Dividend(Base, TimestampMixin):
    __tablename__ = "dividends"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    round_id = Column(BigInteger, ForeignKey("committee_rounds.id", ondelete="CASCADE"), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(BigInteger, ForeignKey("committee_members.id", ondelete="CASCADE"), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    is_paid = Column(Boolean, default=False, nullable=False)

    round = relationship("CommitteeRound", back_populates="dividends")
    member = relationship("CommitteeMember")


# ── 17. Interest Distributions ───────────────────────────
class InterestDistribution(Base, TimestampMixin):
    __tablename__ = "interest_distributions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    round_id = Column(BigInteger, ForeignKey("committee_rounds.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(BigInteger, ForeignKey("committee_members.id", ondelete="CASCADE"), nullable=False)
    principal_amount = Column(Numeric(14, 2), nullable=False)
    interest_rate = Column(Numeric(5, 2), nullable=False)
    interest_amount = Column(Numeric(12, 2), nullable=False)
    is_paid = Column(Boolean, default=False, nullable=False)


# ── 18. Payouts ──────────────────────────────────────────
class Payout(Base, TimestampMixin):
    __tablename__ = "payouts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    round_id = Column(BigInteger, ForeignKey("committee_rounds.id", ondelete="CASCADE"), nullable=False)
    member_id = Column(BigInteger, ForeignKey("committee_members.id", ondelete="CASCADE"), nullable=False)
    gross_amount = Column(Numeric(14, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0, nullable=False)
    net_amount = Column(Numeric(14, 2), nullable=False)
    payment_method = Column(SAEnum(PaymentMethod), nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)
    reference_number = Column(String(100), nullable=True)


# ── 19. Penalties ────────────────────────────────────────
class Penalty(Base, TimestampMixin):
    __tablename__ = "penalties"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(BigInteger, ForeignKey("payments.id"), nullable=True)
    penalty_type = Column(String(50), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(Text, nullable=True)
    is_waived = Column(Boolean, default=False, nullable=False)


# ── 20. Notifications ────────────────────────────────────
class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    notification_type = Column(SAEnum(NotificationType), nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    reference_id = Column(BigInteger, nullable=True)
    reference_type = Column(String(50), nullable=True)

    user = relationship("User", back_populates="notifications")

    __table_args__ = (
        Index("idx_notification_user", "user_id", "is_read"),
    )


# ── 21. Notification Settings ────────────────────────────
class NotificationSetting(Base, TimestampMixin):
    __tablename__ = "notification_settings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    push_enabled = Column(Boolean, default=True, nullable=False)
    email_enabled = Column(Boolean, default=True, nullable=False)
    sms_enabled = Column(Boolean, default=False, nullable=False)
    payment_reminders = Column(Boolean, default=True, nullable=False)
    bid_notifications = Column(Boolean, default=True, nullable=False)
    draw_notifications = Column(Boolean, default=True, nullable=False)


# ── 22. Audit Logs ───────────────────────────────────────
class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    action = Column(SAEnum(AuditAction), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(BigInteger, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON
    new_values = Column(Text, nullable=True)  # JSON
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    user = relationship("User", back_populates="audit_logs")

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
        Index("idx_audit_user", "user_id"),
    )


# ── 23. System Config ────────────────────────────────────
class SystemConfig(Base, TimestampMixin):
    __tablename__ = "system_config"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    config_key = Column(String(100), unique=True, nullable=False)
    config_value = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)


# ── 24. System Logs ──────────────────────────────────────
class SystemLog(Base, TimestampMixin):
    __tablename__ = "system_logs"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    level = Column(String(20), nullable=False)
    module = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    stack_trace = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True)


# ── 25. Rate Limit Tracking ──────────────────────────────
class RateLimitTracker(Base, TimestampMixin):
    __tablename__ = "rate_limit_tracker"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    ip_address = Column(String(45), nullable=False, index=True)
    endpoint = Column(String(255), nullable=False)
    request_count = Column(Integer, default=1, nullable=False)
    window_start = Column(DateTime, nullable=False)


# ── 26. Committee Invitations ────────────────────────────
class CommitteeInvitation(Base, TimestampMixin):
    __tablename__ = "committee_invitations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    invited_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    invited_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    invited_phone = Column(String(20), nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    expires_at = Column(DateTime, nullable=True)


# ── 27. Committee Documents ──────────────────────────────
class CommitteeDocument(Base, TimestampMixin):
    __tablename__ = "committee_documents"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    uploaded_by = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    document_type = Column(String(50), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)


# ── 28. Member Guarantors ────────────────────────────────
class MemberGuarantor(Base, TimestampMixin):
    __tablename__ = "member_guarantors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    member_id = Column(BigInteger, ForeignKey("committee_members.id", ondelete="CASCADE"), nullable=False)
    guarantor_name = Column(String(255), nullable=False)
    guarantor_phone = Column(String(20), nullable=False)
    guarantor_address = Column(Text, nullable=True)
    guarantor_id_proof = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)


# ── 29. Financial Summary ────────────────────────────────
class FinancialSummary(Base, TimestampMixin):
    __tablename__ = "financial_summaries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    round_number = Column(Integer, nullable=False)
    total_collected = Column(Numeric(14, 2), default=0, nullable=False)
    total_paid_out = Column(Numeric(14, 2), default=0, nullable=False)
    total_dividends = Column(Numeric(14, 2), default=0, nullable=False)
    total_interest = Column(Numeric(14, 2), default=0, nullable=False)
    total_penalties = Column(Numeric(14, 2), default=0, nullable=False)
    balance = Column(Numeric(14, 2), default=0, nullable=False)


# ── 30. Member Statements ────────────────────────────────
class MemberStatement(Base, TimestampMixin):
    __tablename__ = "member_statements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    member_id = Column(BigInteger, ForeignKey("committee_members.id", ondelete="CASCADE"), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    total_contributions = Column(Numeric(14, 2), default=0, nullable=False)
    total_payouts = Column(Numeric(14, 2), default=0, nullable=False)
    total_dividends = Column(Numeric(14, 2), default=0, nullable=False)
    total_interest_earned = Column(Numeric(14, 2), default=0, nullable=False)
    total_penalties = Column(Numeric(14, 2), default=0, nullable=False)
    net_profit_loss = Column(Numeric(14, 2), default=0, nullable=False)
    last_updated_round = Column(Integer, default=0, nullable=False)


# ── 31. Committee Analytics ──────────────────────────────
class CommitteeAnalytics(Base, TimestampMixin):
    __tablename__ = "committee_analytics"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    committee_id = Column(BigInteger, ForeignKey("committees.id", ondelete="CASCADE"), nullable=False)
    metric_name = Column(String(100), nullable=False)
    metric_value = Column(Numeric(14, 2), nullable=False)
    metric_date = Column(Date, nullable=False)
    metadata_json = Column(Text, nullable=True)

    __table_args__ = (
        Index("idx_analytics_committee", "committee_id", "metric_name"),
    )


# ── 32. Dashboard Stats ─────────────────────────────────
class DashboardStat(Base, TimestampMixin):
    __tablename__ = "dashboard_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    total_committees = Column(Integer, default=0, nullable=False)
    active_committees = Column(Integer, default=0, nullable=False)
    total_invested = Column(Numeric(14, 2), default=0, nullable=False)
    total_earned = Column(Numeric(14, 2), default=0, nullable=False)
    pending_payments = Column(Integer, default=0, nullable=False)
    next_payment_date = Column(Date, nullable=True)


# ── 33. FCM Tokens (Push Notifications for Flutter) ─────
class FCMToken(Base, TimestampMixin):
    __tablename__ = "fcm_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(500), nullable=False)
    device_type = Column(String(20), nullable=True)  # android, ios
    is_active = Column(Boolean, default=True, nullable=False)


# ── 34. Report Exports ───────────────────────────────────
class ReportExport(Base, TimestampMixin):
    __tablename__ = "report_exports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    report_type = Column(String(50), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id"), nullable=True)
    file_url = Column(String(500), nullable=True)
    status = Column(String(20), default="pending", nullable=False)
    parameters_json = Column(Text, nullable=True)


# ── 35. Complaint / Support Tickets ──────────────────────
class SupportTicket(Base, TimestampMixin):
    __tablename__ = "support_tickets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    committee_id = Column(BigInteger, ForeignKey("committees.id"), nullable=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    status = Column(String(20), default="open", nullable=False)
    priority = Column(String(20), default="medium", nullable=False)
    assigned_to = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
