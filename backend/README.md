# Committee / Chit Fund Management Platform — Backend API

Production-level backend for managing rotating savings committees (chit funds) with support for Lucky Draw, Bidding, and Percentage/Interest based committee types.

## Tech Stack

- **Framework:** Python FastAPI
- **Database:** MySQL (database name: `committee`)
- **ORM:** SQLAlchemy 2.0
- **Auth:** JWT (PyJWT) + bcrypt password hashing
- **Validation:** Pydantic v2

## Project Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── config/
│   │   └── settings.py          # Application configuration
│   ├── database/
│   │   └── connection.py        # SQLAlchemy engine & session
│   ├── models/
│   │   ├── enums.py             # All enum types
│   │   ├── base.py              # Timestamp mixin
│   │   └── models.py            # 35 SQLAlchemy models
│   ├── schemas/
│   │   ├── common.py            # API response schemas
│   │   ├── auth.py              # Auth request/response schemas
│   │   ├── committee.py         # Committee schemas
│   │   ├── member.py            # Member schemas
│   │   ├── bidding.py           # Bidding schemas
│   │   ├── luckydraw.py         # Lucky draw schemas
│   │   ├── payment.py           # Payment & transaction schemas
│   │   ├── report.py            # Report schemas
│   │   └── notification.py      # Notification schemas
│   ├── routers/
│   │   ├── auth_router.py       # POST /api/auth/*
│   │   ├── committee_router.py  # /api/committees/*
│   │   ├── member_router.py     # /api/members/*
│   │   ├── bidding_router.py    # /api/bids/*
│   │   ├── luckydraw_router.py  # /api/luckydraw/*
│   │   ├── payment_router.py    # /api/payments/*
│   │   ├── transaction_router.py# /api/transactions/*
│   │   ├── report_router.py     # /api/reports/*
│   │   └── notification_router.py # /api/notifications/*
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── committee_service.py
│   │   ├── member_service.py
│   │   ├── bidding_service.py
│   │   ├── luckydraw_service.py
│   │   ├── payment_service.py
│   │   ├── transaction_service.py
│   │   ├── calculation_engine.py # Automatic financial calculations
│   │   ├── report_service.py
│   │   └── notification_service.py
│   ├── middlewares/
│   │   ├── auth_middleware.py    # JWT auth + role-based access
│   │   ├── logging_middleware.py # Request logging
│   │   ├── rate_limit_middleware.py
│   │   └── error_handler.py     # Global error handling
│   └── utils/
│       ├── security.py          # JWT token creation/verification
│       ├── hashing.py           # bcrypt password hashing
│       └── otp.py               # OTP generation
├── database/
│   └── schema.sql               # Complete MySQL schema (35 tables)
├── requirements.txt
├── .env.example
└── README.md
```

## Setup & Run

### 1. Create MySQL Database

```sql
CREATE DATABASE committee CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Or run the full schema:

```bash
mysql -u root -p < database/schema.sql
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your MySQL credentials and JWT secret
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the Server

```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 5. Access Swagger Docs

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login & get JWT token |
| POST | `/api/auth/logout` | Invalidate session |
| POST | `/api/auth/verify-otp` | Verify OTP |

### Committee Management (Admin)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/committees/create` | Create committee |
| GET | `/api/committees` | List committees |
| GET | `/api/committees/{id}` | Committee details |
| PUT | `/api/committees/update` | Update committee |
| DELETE | `/api/committees/delete` | Soft delete committee |

### Member Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/members/join` | Request to join |
| GET | `/api/members/list` | List members |
| POST | `/api/members/approve` | Approve member (Admin) |
| POST | `/api/members/reject` | Reject member (Admin) |

### Bidding System
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bids/start-round` | Start bidding round (Admin) |
| POST | `/api/bids/place` | Place a bid |
| POST | `/api/bids/close-round` | Close round & determine winner (Admin) |
| GET | `/api/bids/history` | Bid history |

### Lucky Draw System
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/luckydraw/run` | Run lucky draw (Admin) |
| GET | `/api/luckydraw/history` | Draw history |

### Payments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/pay` | Make payment |
| GET | `/api/payments/history` | Payment history |
| GET | `/api/payments/schedule` | Payment schedule |

### Transactions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions/member` | Member transactions |
| GET | `/api/transactions/committee` | Committee transactions |

### Reports & Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/member-statement` | Member financial statement |
| GET | `/api/reports/committee` | Committee report (Admin) |
| GET | `/api/reports/admin-dashboard` | Admin dashboard (Admin) |
| GET | `/api/reports/member-dashboard` | Member dashboard |

### Notifications
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/notifications` | Get notifications |
| POST | `/api/notifications/mark-read` | Mark as read |
| POST | `/api/notifications/mark-all-read` | Mark all read |

## API Response Format

All responses follow a standard JSON format for Flutter integration:

```json
{
  "status": true,
  "message": "Login successful",
  "token": "JWT_TOKEN",
  "user": {
    "id": 1,
    "name": "Ajay"
  }
}
```

Paginated responses include:

```json
{
  "status": true,
  "message": "Data fetched",
  "data": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

## Database Tables (35)

1. users
2. user_profiles
3. user_sessions
4. otp_verifications
5. committees
6. committee_settings
7. committee_members
8. committee_rounds
9. bids
10. bid_settings
11. lucky_draws
12. lucky_draw_history
13. payments
14. payment_schedules
15. transactions
16. dividends
17. interest_distributions
18. payouts
19. penalties
20. notifications
21. notification_settings
22. audit_logs
23. system_config
24. system_logs
25. rate_limit_tracker
26. committee_invitations
27. committee_documents
28. member_guarantors
29. financial_summaries
30. member_statements
31. committee_analytics
32. dashboard_stats
33. fcm_tokens
34. report_exports
35. support_tickets

## Calculation Engine

Automatic calculations stored in the database:

| Calculation | Formula |
|-------------|---------|
| Monthly Pool | `members × monthlyContribution` |
| Winner Payout | `committeeAmount − bidDiscount` |
| Dividend/Member | `discount ÷ remainingMembers` |
| Interest Payment | `committeeAmount × interestRate` |
