# Leave Management System - API Endpoints Documentation

## Overview

This document provides a comprehensive guide to all available API endpoints in the Leave Management System backend. The API uses Django REST Framework with JWT authentication.

---

## Authentication

### Login

**Endpoint:** `POST /auth/login/`

- Authenticate employee with email and password
- Returns access token, refresh token, and employee information
- Required for all authenticated endpoints

### Logout

**Endpoint:** `POST /auth/logout/`

- Revoke current session
- Requires: Access token

### Set/Reset Password

**Endpoint:** `POST /auth/set-password/`

- Set new password after clicking reset link
- Used during initial setup or password recovery

### Token Refresh

**Endpoint:** `POST /auth/token/refresh/`

- Refresh expired access token
- Accepts: Refresh token

### Get Current User Profile

**Endpoint:** `GET /auth/me/`

- Retrieve authenticated user's profile information
- Requires: Access token

---

## 📋 Leaves Endpoints

### List All Leaves

**Endpoint:** `GET /leaves/`

- **Permissions:** Authenticated users
- **Behavior:**
  - Employees: See only their own leaves
  - HR/Admin/Manager: See all leaves
- **Query Parameters:**
  - `search`: Filter by leave type, status, employee email/name
- **Returns:** List of leave requests with details

### Create Leave Request

**Endpoint:** `POST /leaves/`

- **Permissions:** Authenticated users
- **Request Body:**

  ```json
  {
    "leave_type": "id",
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "reason": "string"
  }
  ```

- **Returns:** Created leave request details

### Retrieve Leave Details

**Endpoint:** `GET /leaves/<id>/`

- **Permissions:** Authenticated users
- **Returns:** Specific leave request details

### Update Leave (Full)

**Endpoint:** `PUT /leaves/<id>/`

- **Permissions:** Authenticated users
- **Returns:** Updated leave request

### Update Leave (Partial)

**Endpoint:** `PATCH /leaves/<id>/`

- **Permissions:** Authenticated users
- **Returns:** Updated leave request

### Cancel Leave Request

**Endpoint:** `DELETE /leaves/<id>/`

- **Permissions:** Authenticated users
- **Behavior:** Sets leave status to "Cancelled" (soft delete)
- Only pending or approved leaves can be cancelled

### Update Leave Status (HR/Admin Only)

**Endpoint:** `PATCH /leaves/<id>/update_status/`

- **Permissions:** HR, Admin roles
- **Request Body:**

  ```json
  {
    "status": "APPROVED|REJECTED|PENDING",
    "admin_remarks": "string (optional)"
  }
  ```

- **Returns:** Updated leave with status and remarks

### Employee Cancel Own Leave

**Endpoint:** `PATCH /leaves/<id>/cancel/`

- **Permissions:** Authenticated users (owner only)
- **Behavior:** Allows employees to cancel their pending leaves
- Returns 403 if not leave owner
- Returns 400 if leave is not pending

### List Pending Leaves

**Endpoint:** `GET /leaves/pending_leaves/`

- **Permissions:** HR, Admin roles
- **Returns:** All leaves with pending status

### Get Current User's Leaves

**Endpoint:** `GET /leaves/by_employee/`

- **Permissions:** Authenticated users
- **Returns:** All leaves belonging to current user

---

## 👤 Employees Endpoints

### List All Employees

**Endpoint:** `GET /employees/`

- **Permissions:** Authenticated, HR/Admin only
- **Query Parameters:**
  - `search`: Filter by email, name, department, position, role
- **Returns:** List of all employees

### Create New Employee

**Endpoint:** `POST /employees/`

- **Permissions:** Authenticated, HR/Admin only
- **Request Body:**

  ```json
  {
    "email": "employee@example.com",
    "first_name": "string",
    "last_name": "string",
    "department": "string",
    "position": "string",
    "role": "EMPLOYEE|HR|MANAGER|ADMIN",
    "institution": "id"
  }
  ```

- **Returns:** Created employee details with welcome email sent

### Retrieve Employee Details

**Endpoint:** `GET /employees/<id>/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:** Specific employee details

### Update Employee (Full)

**Endpoint:** `PUT /employees/<id>/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:** Updated employee

### Update Employee (Partial)

**Endpoint:** `PATCH /employees/<id>/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:** Updated employee

### Deactivate Employee

**Endpoint:** `DELETE /employees/<id>/`

- **Permissions:** Authenticated, HR/Admin only
- **Behavior:** Sets `is_active` to False (soft delete)

### Get Employee's Leaves

**Endpoint:** `GET /employees/<id>/leaves/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:** All leave requests for specific employee

### Toggle Employee Active Status

**Endpoint:** `PATCH /employees/<id>/toggle_active/`

- **Permissions:** Authenticated, HR/Admin only
- **Behavior:** Toggles employee active/inactive status
- **Returns:** Success message with new status

### Resend Welcome Email

**Endpoint:** `POST /employees/<id>/resend_welcome_email/`

- **Permissions:** Authenticated, HR/Admin only
- **Behavior:** Sends password reset link to employee
- Cannot send to inactive employees
- **Returns:** Success message

---

## 🏥 Leave Types Endpoints

### List All Leave Types

**Endpoint:** `GET /leave-types/`

- **Permissions:** Authenticated users
- **Query Parameters:**
  - `search`: Filter by name
- **Returns:** List of all leave types

### Create Leave Type

**Endpoint:** `POST /leave-types/`

- **Permissions:** Authenticated, HR/Admin only
- **Request Body:**

  ```json
  {
    "name": "string",
    "description": "string (optional)",
    "days_allowed": "integer"
  }
  ```

- **Returns:** Created leave type

### Retrieve Leave Type Details

**Endpoint:** `GET /leave-types/<id>/`

- **Permissions:** Authenticated users
- **Returns:** Specific leave type details

### Update Leave Type (Full)

**Endpoint:** `PUT /leave-types/<id>/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:** Updated leave type

### Update Leave Type (Partial)

**Endpoint:** `PATCH /leave-types/<id>/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:** Updated leave type

### Delete Leave Type

**Endpoint:** `DELETE /leave-types/<id>/`

- **Permissions:** Authenticated, HR/Admin only
- **Behavior:** Only allowed if no leaves exist with this type
- **Returns:** 400 if leave type is in use

### Toggle Leave Type Active Status

**Endpoint:** `PATCH /leave-types/<id>/toggle_active/`

- **Permissions:** Authenticated, HR/Admin only
- **Behavior:** Toggles leave type active/inactive status
- **Returns:** Success message with new status

---

## 🏢 Institutions Endpoints

### List All Institutions

**Endpoint:** `GET /institutions/`

- **Permissions:** Authenticated, Admin only
- **Query Parameters:**
  - `search`: Filter by name, location
- **Returns:** List of all institutions

### Create Institution

**Endpoint:** `POST /institutions/`

- **Permissions:** Authenticated, Admin only
- **Request Body:**

  ```json
  {
    "name": "string"
  }
  ```

- **Returns:** Created institution

### Retrieve Institution Details

**Endpoint:** `GET /institutions/<id>/`

- **Permissions:** Authenticated, Admin only
- **Returns:** Specific institution details

### Update Institution (Full)

**Endpoint:** `PUT /institutions/<id>/`

- **Permissions:** Authenticated, Admin only
- **Returns:** Updated institution

### Update Institution (Partial)

**Endpoint:** `PATCH /institutions/<id>/`

- **Permissions:** Authenticated, Admin only
- **Returns:** Updated institution

### Delete Institution

**Endpoint:** `DELETE /institutions/<id>/`

- **Permissions:** Authenticated, Admin only
- **Behavior:** Only allowed if no active employees exist
- **Returns:** 400 if institution has active employees

### List Institution Employees

**Endpoint:** `GET /institutions/<id>/employees/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:** All active employees in institution

### Get Active Employee Count

**Endpoint:** `GET /institutions/<id>/employee_count/`

- **Permissions:** Authenticated, HR/Admin only
- **Returns:**

  ```json
  {
    "employee_count": "integer"
  }
  ```

### Toggle Institution Active Status

**Endpoint:** `PATCH /institutions/<id>/toggle_active/`

- **Permissions:** Authenticated, Admin only
- **Behavior:** Toggles institution active/inactive status
- **Returns:** Success message with new status

---

## Response Format

### Success Response

```json
{
  "id": "integer",
  "field1": "value1",
  "field2": "value2",
  ...
}

```

### Error Response

```json
{
  "error": "Error message",
  "detail": "Detailed error information (if available)"
}
```

### List Response

```json
[
  {
    "id": "integer",
    "field1": "value1",
    ...
  },
  ...
]
```

---

## Status Codes

| Code | Meaning |
|------|---------|

| 200 | OK - Request successful |
| 201 | Created - Resource created |
| 204 | No Content - Request successful, no content to return |
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Authentication required or failed |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource not found |
| 500 | Internal Server Error - Server error |

---

## Permission Levels

### EMPLOYEE

- View own leaves
- Create leave requests
- Cancel own pending leaves
- View profile

### HR

- View/manage all leaves
- Create/update/delete leave types
- Create/manage employees (not admins)
- Update leave statuses with remarks

### MANAGER

- View all leaves (same as HR)
- View employee information

### ADMIN

- Full access to all endpoints
- Manage institutions
- Create/manage HR accounts
- System-wide operations

---

## Common Use Cases

### Employee Apply for Leave

1. `GET /leave-types/` - Get available leave types
2. `POST /leaves/` - Submit leave request
3. Employee enters: leave type, dates, reason

### HR Approve Leaves

1. `GET /leaves/pending_leaves/` - List pending requests
2. `PATCH /leaves/<id>/update_status/` - Approve/Reject with remarks

### Create New Employe

1. `POST /employees/` - Create employee record
2. System sends welcome email with password reset link
3. Employee clicks link and sets password via `POST /auth/set-password/`

### Search Employees

1. `GET /employees/?search=email_or_name` - Filter employees

---

## Authentication Headers

All authenticated endpoints require:

``` http
Authorization: Bearer <access_token>
Content-Type: application/json
```

---

## Pagination & Filtering

- **Search:** Pass `search` query parameter with keywords
- **Pagination:** Use `limit` and `offset` query parameters (if enabled)
- **Ordering:** Use `ordering` query parameter with field name

---

## Error Handling

Check the response status code and error message:

- **400** - Review request parameters and format
- **401** - Re-authenticate or refresh token
- **403** - Check user role/permissions
- **404** - Verify resource ID exists
- **500** - Contact system administrator

---

**Last Updated:** March 2026
**Version:** 1.0
