# Committee Management Platform — API Collection

**Base URL:** `http://localhost:8000`  
**Version:** `1.0.0`  
**Auth:** Bearer Token (JWT) — pass as `Authorization: Bearer <token>`

---

## Table of Contents

1. [Health Check](#1-health-check)
2. [Authentication](#2-authentication)
3. [Committee Management](#3-committee-management)
4. [Member Management](#4-member-management)
5. [Bidding System](#5-bidding-system)
6. [Lucky Draw System](#6-lucky-draw-system)
7. [Payment Management](#7-payment-management)
8. [Financial Transactions](#8-financial-transactions)
9. [Notifications](#9-notifications)
10. [Reporting & Dashboards](#10-reporting--dashboards)
11. [Enums Reference](#11-enums-reference)

---

## Common Response Format

All endpoints return a standard envelope:

```json
{
  "status": true,
  "message": "Success message",
  "data": { ... }
}
```

Paginated endpoints add:

```json
{
  "status": true,
  "message": "...",
  "data": [ ... ],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "total_pages": 5
}
```

Validation errors return **422**:

```json
{
  "status": false,
  "message": "Validation error",
  "errors": [
    { "field": "body → email", "message": "value is not a valid email address" }
  ]
}
```

---

## 1. Health Check

### `GET /`

Check if the API is running.

| Field | Value |
|-------|-------|
| Auth | None |

**Response:**

```json
{
  "status": true,
  "message": "Committee Management Platform API is running",
  "version": "1.0.0"
}
```

---

## 2. Authentication

### 2.1 Register

`POST /api/auth/register`

| Field | Value |
|-------|-------|
| Auth | None |
| Content-Type | application/json |

**Request Body:**

```json
{
  "name": "Ajay Kumar",
  "email": "ajay@example.com",
  "phone": "9876543210",
  "password": "secret123",
  "role": "member"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | min: 2, max: 255 |
| `email` | string (email) | Yes | Valid email |
| `phone` | string | Yes | min: 10, max: 20 |
| `password` | string | Yes | min: 6, max: 128 |
| `role` | string | No | `admin` / `member` (default: `member`) |

---

### 2.2 Login

`POST /api/auth/login`

| Field | Value |
|-------|-------|
| Auth | None |
| Content-Type | application/json |

**Request Body:**

```json
{
  "email": "ajay@example.com",
  "password": "secret123"
}
```

**Response:**

```json
{
  "status": true,
  "message": "Login successful",
  "token": "eyJhbGci...",
  "refresh_token": "eyJhbGci...",
  "user": {
    "id": 1,
    "name": "Ajay Kumar",
    "email": "ajay@example.com",
    "phone": "9876543210",
    "role": "member",
    "status": "active",
    "is_verified": true,
    "avatar_url": null,
    "city": null,
    "state": null,
    "created_at": "2026-03-01T10:00:00"
  }
}
```

> The server captures `User-Agent` header and client IP automatically.

---

### 2.3 Verify OTP

`POST /api/auth/verify-otp`

| Field | Value |
|-------|-------|
| Auth | None |
| Content-Type | application/json |

**Request Body:**

```json
{
  "user_id": 1,
  "otp_code": "123456",
  "otp_type": "registration"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `user_id` | int | Yes | — |
| `otp_code` | string | Yes | min: 4, max: 10 |
| `otp_type` | string | No | default: `registration` |

---

### 2.4 Logout

`POST /api/auth/logout`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

No request body required. The token is read from the `Authorization` header.

---

## 3. Committee Management

> All endpoints require **Bearer Token**. Create / Update / Delete require **Admin** role.

### 3.1 Create Committee

`POST /api/committees/create`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "name": "Gold Committee 2026",
  "description": "Monthly gold savings committee",
  "committee_type": "bidding",
  "total_members": 20,
  "monthly_contribution": 5000.00,
  "duration_months": 20,
  "start_date": "2026-04-01",
  "interest_rate": 2.5,
  "min_bid_amount": 1000.00,
  "max_bid_amount": 10000.00,
  "rules": "Payment due by 5th of each month"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | Yes | min: 2, max: 255 |
| `description` | string | No | — |
| `committee_type` | string | Yes | `lucky_draw` / `bidding` / `percentage` |
| `total_members` | int | Yes | 2 – 100 |
| `monthly_contribution` | decimal | Yes | > 0 |
| `duration_months` | int | Yes | 2 – 100 |
| `start_date` | date | No | `YYYY-MM-DD` |
| `interest_rate` | decimal | No | 0 – 100 (default: 0) |
| `min_bid_amount` | decimal | No | — |
| `max_bid_amount` | decimal | No | — |
| `rules` | string | No | — |

---

### 3.2 List Committees

`GET /api/committees`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Default | Validation |
|-------|------|---------|------------|
| `page` | int | 1 | ≥ 1 |
| `page_size` | int | 20 | 1 – 100 |

**Example:** `GET /api/committees?page=1&page_size=10`

---

### 3.3 Get Committee by ID

`GET /api/committees/{committee_id}`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Path Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `committee_id` | int | Yes |

**Example:** `GET /api/committees/5`

---

### 3.4 Update Committee

`PUT /api/committees/update?committee_id={id}`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |
| Content-Type | application/json |

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `committee_id` | int | Yes |

**Request Body (all fields optional):**

```json
{
  "name": "Updated Committee Name",
  "description": "New description",
  "status": "active",
  "start_date": "2026-05-01",
  "interest_rate": 3.0,
  "min_bid_amount": 1500.00,
  "max_bid_amount": 12000.00,
  "rules": "Updated rules"
}
```

| Field | Type | Validation |
|-------|------|------------|
| `name` | string | min: 2, max: 255 |
| `description` | string | — |
| `status` | string | `draft` / `active` / `completed` / `cancelled` |
| `start_date` | date | `YYYY-MM-DD` |
| `interest_rate` | decimal | — |
| `min_bid_amount` | decimal | — |
| `max_bid_amount` | decimal | — |
| `rules` | string | — |

---

### 3.5 Delete Committee

`DELETE /api/committees/delete?committee_id={id}`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `committee_id` | int | Yes |

---

## 4. Member Management

> All endpoints require **Bearer Token**. Approve / Reject require **Admin** role.

### 4.1 Join Committee

`POST /api/members/join`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "committee_id": 5
}
```

---

### 4.2 List Members

`GET /api/members/list`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `committee_id` | int | Yes | — | — |
| `page` | int | No | 1 | ≥ 1 |
| `page_size` | int | No | 20 | 1 – 100 |

**Example:** `GET /api/members/list?committee_id=5&page=1&page_size=10`

---

### 4.3 Approve Member

`POST /api/members/approve`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "member_id": 12,
  "slot_number": 3
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `member_id` | int | Yes | Membership record ID |
| `slot_number` | int | No | Assign a specific slot |

---

### 4.4 Reject Member

`POST /api/members/reject?member_id={id}`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `member_id` | int | Yes |

---

## 5. Bidding System

> Used for committees with `committee_type = "bidding"`.

### 5.1 Start Round

`POST /api/bids/start-round`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "committee_id": 5
}
```

---

### 5.2 Place Bid

`POST /api/bids/place`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "round_id": 10,
  "bid_amount": 4500.00
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `round_id` | int | Yes | — |
| `bid_amount` | decimal | Yes | > 0 |

---

### 5.3 Close Round

`POST /api/bids/close-round`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "round_id": 10
}
```

---

### 5.4 Bid History

`GET /api/bids/history`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `committee_id` | int | Yes | — | — |
| `page` | int | No | 1 | ≥ 1 |
| `page_size` | int | No | 20 | 1 – 100 |

**Example:** `GET /api/bids/history?committee_id=5&page=1&page_size=10`

---

## 6. Lucky Draw System

> Used for committees with `committee_type = "lucky_draw"`.

### 6.1 Run Lucky Draw

`POST /api/luckydraw/run`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "committee_id": 5,
  "round_id": 10
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `committee_id` | int | Yes | Must be an **active** lucky-draw committee ID |
| `round_id` | int | Yes | Accepts committee round **table ID** or **round number** (e.g., `1` for first round) |

> Precondition: The resolved round must be in `pending` status.

---

### 6.2 Lucky Draw History

`GET /api/luckydraw/history`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `committee_id` | int | Yes | — | — |
| `page` | int | No | 1 | ≥ 1 |
| `page_size` | int | No | 20 | 1 – 100 |

---

## 7. Payment Management

### 7.1 Make Payment

`POST /api/payments/pay`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "committee_id": 5,
  "round_number": 3,
  "amount": 5000.00,
  "payment_method": "upi",
  "reference_number": "UPI123456789",
  "notes": "March contribution"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `committee_id` | int | Yes | — |
| `round_number` | int | Yes | — |
| `amount` | decimal | Yes | > 0 |
| `payment_method` | string | Yes | `cash` / `bank_transfer` / `upi` / `cheque` / `online` |
| `reference_number` | string | No | — |
| `notes` | string | No | — |

---

### 7.2 Payment History

`GET /api/payments/history`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `committee_id` | int | No | null | Filter by committee |
| `page` | int | No | 1 | ≥ 1 |
| `page_size` | int | No | 20 | 1 – 100 |

**Example:** `GET /api/payments/history?committee_id=5&page=1`

---

### 7.3 Payment Schedule

`GET /api/payments/schedule`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `committee_id` | int | Yes |

**Example:** `GET /api/payments/schedule?committee_id=5`

---

## 8. Financial Transactions

### 8.1 Member Transactions

`GET /api/transactions/member`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

Returns the current user's transaction log.

**Query Parameters:**

| Param | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `committee_id` | int | No | null | Filter by committee |
| `page` | int | No | 1 | ≥ 1 |
| `page_size` | int | No | 20 | 1 – 100 |

---

### 8.2 Committee Transactions

`GET /api/transactions/committee`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Required | Default | Validation |
|-------|------|----------|---------|------------|
| `committee_id` | int | Yes | — | — |
| `page` | int | No | 1 | ≥ 1 |
| `page_size` | int | No | 20 | 1 – 100 |

---

## 9. Notifications

### 9.1 Get Notifications

`GET /api/notifications`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Default | Validation |
|-------|------|---------|------------|
| `page` | int | 1 | ≥ 1 |
| `page_size` | int | 20 | 1 – 100 |

---

### 9.2 Mark Notifications as Read

`POST /api/notifications/mark-read`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |
| Content-Type | application/json |

**Request Body:**

```json
{
  "notification_ids": [1, 2, 3]
}
```

---

### 9.3 Mark All Notifications as Read

`POST /api/notifications/mark-all-read`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

No request body required.

---

## 10. Reporting & Dashboards

### 10.1 Member Statement

`GET /api/reports/member-statement`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `committee_id` | int | Yes |

**Response Data:**

```json
{
  "member_id": 1,
  "committee_id": 5,
  "user_name": "Ajay Kumar",
  "committee_name": "Gold Committee 2026",
  "total_contributions": 25000.00,
  "total_payouts": 50000.00,
  "total_dividends": 1200.00,
  "total_interest_earned": 500.00,
  "total_penalties": 100.00,
  "net_profit_loss": 26600.00
}
```

---

### 10.2 Committee Report

`GET /api/reports/committee`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |

**Query Parameters:**

| Param | Type | Required |
|-------|------|----------|
| `committee_id` | int | Yes |

**Response Data:**

```json
{
  "committee_id": 5,
  "committee_name": "Gold Committee 2026",
  "total_collected": 500000.00,
  "total_paid_out": 450000.00,
  "total_dividends": 10000.00,
  "total_interest": 5000.00,
  "total_penalties": 2000.00,
  "balance": 47000.00,
  "rounds_completed": 10,
  "total_rounds": 20
}
```

---

### 10.3 Admin Dashboard

`GET /api/reports/admin-dashboard`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token (Admin)** |

No query parameters.

**Response Data:**

```json
{
  "total_committees": 15,
  "active_committees": 8,
  "total_members": 200,
  "total_collections": 1500000.00,
  "total_payouts": 1200000.00,
  "pending_payments": 25,
  "overdue_payments": 5
}
```

---

### 10.4 Member Dashboard

`GET /api/reports/member-dashboard`

| Field | Value |
|-------|-------|
| Auth | **Bearer Token** |

No query parameters.

**Response Data:**

```json
{
  "total_committees": 3,
  "active_committees": 2,
  "total_invested": 75000.00,
  "total_earned": 52000.00,
  "pending_payments": 2,
  "next_payment_date": "2026-04-05"
}
```

---

## 11. Enums Reference

### User Role
| Value | Description |
|-------|-------------|
| `admin` | Platform administrator |
| `member` | Regular member |

### User Status
| Value |
|-------|
| `active` |
| `inactive` |
| `suspended` |
| `pending` |

### Committee Type
| Value | Description |
|-------|-------------|
| `lucky_draw` | Winner selected randomly each round |
| `bidding` | Members bid for the pool each round |
| `percentage` | Percentage-based distribution |

### Committee Status
| Value |
|-------|
| `draft` |
| `active` |
| `completed` |
| `cancelled` |

### Membership Status
| Value |
|-------|
| `pending` |
| `approved` |
| `rejected` |
| `left` |
| `removed` |

### Payment Status
| Value |
|-------|
| `pending` |
| `paid` |
| `late` |
| `missed` |
| `partial` |

### Payment Method
| Value |
|-------|
| `cash` |
| `bank_transfer` |
| `upi` |
| `cheque` |
| `online` |

### Transaction Type
| Value |
|-------|
| `contribution` |
| `payout` |
| `dividend` |
| `interest` |
| `penalty` |
| `refund` |

### Round Status
| Value |
|-------|
| `pending` |
| `in_progress` |
| `completed` |
| `cancelled` |

### Notification Type
| Value |
|-------|
| `payment_reminder` |
| `payment_received` |
| `bid_started` |
| `bid_won` |
| `lucky_draw_result` |
| `committee_joined` |
| `committee_started` |
| `payout_processed` |
| `general` |

---

## Quick Reference — All Endpoints

| # | Method | Endpoint | Auth | Role |
|---|--------|----------|------|------|
| 1 | `GET` | `/` | — | — |
| 2 | `POST` | `/api/auth/register` | — | — |
| 3 | `POST` | `/api/auth/login` | — | — |
| 4 | `POST` | `/api/auth/verify-otp` | — | — |
| 5 | `POST` | `/api/auth/logout` | Token | Any |
| 6 | `POST` | `/api/committees/create` | Token | Admin |
| 7 | `GET` | `/api/committees` | Token | Any |
| 8 | `GET` | `/api/committees/{committee_id}` | Token | Any |
| 9 | `PUT` | `/api/committees/update?committee_id=` | Token | Admin |
| 10 | `DELETE` | `/api/committees/delete?committee_id=` | Token | Admin |
| 11 | `POST` | `/api/members/join` | Token | Any |
| 12 | `GET` | `/api/members/list?committee_id=` | Token | Any |
| 13 | `POST` | `/api/members/approve` | Token | Admin |
| 14 | `POST` | `/api/members/reject?member_id=` | Token | Admin |
| 15 | `POST` | `/api/bids/start-round` | Token | Admin |
| 16 | `POST` | `/api/bids/place` | Token | Any |
| 17 | `POST` | `/api/bids/close-round` | Token | Admin |
| 18 | `GET` | `/api/bids/history?committee_id=` | Token | Any |
| 19 | `POST` | `/api/luckydraw/run` | Token | Admin |
| 20 | `GET` | `/api/luckydraw/history?committee_id=` | Token | Any |
| 21 | `POST` | `/api/payments/pay` | Token | Any |
| 22 | `GET` | `/api/payments/history` | Token | Any |
| 23 | `GET` | `/api/payments/schedule?committee_id=` | Token | Any |
| 24 | `GET` | `/api/transactions/member` | Token | Any |
| 25 | `GET` | `/api/transactions/committee?committee_id=` | Token | Any |
| 26 | `GET` | `/api/notifications` | Token | Any |
| 27 | `POST` | `/api/notifications/mark-read` | Token | Any |
| 28 | `POST` | `/api/notifications/mark-all-read` | Token | Any |
| 29 | `GET` | `/api/reports/member-statement?committee_id=` | Token | Any |
| 30 | `GET` | `/api/reports/committee?committee_id=` | Token | Admin |
| 31 | `GET` | `/api/reports/admin-dashboard` | Token | Admin |
| 32 | `GET` | `/api/reports/member-dashboard` | Token | Any |

---

> **Docs UI:** `http://localhost:8000/docs` (Swagger) · `http://localhost:8000/redoc` (ReDoc)
