# API Specification

## Overview

The Personal Analytics Dashboard API is built with FastAPI and provides RESTful endpoints for task management, scheduling, user authentication, and analytics.

**Base URL**: `http://127.0.0.1:8000` (development)

**Interactive Docs**: `http://127.0.0.1:8000/docs` (Swagger UI)

**Alternative Docs**: `http://127.0.0.1:8000/redoc` (ReDoc)

## Authentication

All API endpoints (except registration and login) require authentication via JWT token.

**Header**: `Authorization: Bearer <token>`

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "name": "User Name"
}
```

**Response**: User object with JWT token

#### POST /auth/login
Authenticate user and get JWT token.

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response**:
```json
{
  "access_token": "jwt_token_here",
  "token_type": "bearer",
  "user": {...}
}
```

#### POST /auth/refresh
Refresh JWT token.

#### POST /auth/logout
Invalidate current session.

## Task Management

#### GET /tasks/
Get user's tasks with optional filtering.

**Query Parameters**:
- `completed`: boolean
- `date_from`: YYYY-MM-DD
- `date_to`: YYYY-MM-DD
- `limit`: integer
- `offset`: integer

**Response**: Array of task objects

#### POST /tasks/
Create a new task.

**Request Body**:
```json
{
  "title": "Task Title",
  "description": "Task description",
  "due_date": "2024-12-31",
  "estimated_duration": 60,
  "importance": "high",
  "category": "work"
}
```

#### GET /tasks/{task_id}
Get specific task details.

#### PUT /tasks/{task_id}
Update task.

#### DELETE /tasks/{task_id}
Delete task.

## Schedule Management

#### GET /schedules/today
Get today's schedule.

**Response**:
```json
{
  "date": "2024-01-15",
  "tasks": [
    {
      "id": 1,
      "title": "Morning Meeting",
      "start_time": "09:00",
      "end_time": "10:00",
      "type": "appointment"
    }
  ],
  "breaks": [...],
  "feedback_submitted": false
}
```

#### GET /schedules/week
Get weekly schedule overview.

#### POST /schedules/feedback
Submit feedback for today's schedule.

**Request Body**:
```json
{
  "rating": "balanced",  // "balanced" | "stressed" | "underwhelmed"
  "comments": "Optional feedback text"
}
```

## User Management

#### GET /users/me
Get current user profile.

#### PUT /users/me
Update user profile.

#### POST /users/me/change-password
Change password.

#### POST /auth/2fa/enable
Enable 2FA.

#### POST /auth/2fa/verify
Verify 2FA setup.

#### POST /auth/2fa/disable
Disable 2FA.

## Analytics

#### GET /analytics/productivity
Get productivity metrics.

**Response**:
```json
{
  "completion_rate": 0.85,
  "average_tasks_per_day": 8,
  "stress_trend": "decreasing",
  "preferred_work_hours": "9-17"
}
```

#### GET /analytics/schedule-history
Get historical schedule data.

## Admin Endpoints (Admin Users Only)

#### GET /admin/users
List all users.

#### POST /admin/users/{user_id}/deactivate
Deactivate user.

#### GET /admin/analytics/system
System-wide analytics.

#### POST /admin/ml/train
Trigger ML model training.

## Error Responses

All endpoints return standard HTTP status codes:

- `200`: Success
- `201`: Created
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

Error response format:
```json
{
  "detail": "Error message",
  "errors": [...]  // For validation errors
}
```

## Rate Limiting

- Authenticated requests: 1000/hour
- Unauthenticated requests: 100/hour
- Admin requests: 500/hour

## WebSocket Support

Real-time updates via WebSocket at `/ws/schedules`

**Message Types**:
- `schedule_updated`: Schedule changes
- `task_completed`: Task status changes
- `notification`: System notifications

## SDKs and Libraries

- **Python Client**: `pip install personal-analytics-client`
- **JavaScript Client**: Available via npm
- **Postman Collection**: Available in repository

## Versioning

API version is included in URL path: `/v1/...`

Current version: v1

## Support

For API support:
- Interactive docs at `/docs`
- GitHub Issues for bugs/features
- Email: support@personal-analytics.com