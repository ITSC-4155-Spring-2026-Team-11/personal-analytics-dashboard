# System Architecture

## Overview

The Personal Analytics Dashboard is a cross-platform application designed to generate optimized daily schedules based on user tasks, appointments, and feedback. It uses a hybrid approach combining rule-based scheduling with machine learning for personalization.

## High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Client    │    │ Desktop Client  │    │   Tauri App     │
│   (React/Vite)  │    │   (PySide6)     │    │   (React/Web)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │     Backend API     │
                    │    (FastAPI/Python) │
                    │                     │
                    │ - Task Management   │
                    │ - Schedule Generation│
                    │ - User Feedback     │
                    │ - ML Optimization   │
                    └─────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │     Database        │
                    │   (SQLite/MySQL)    │
                    └─────────────────────┘
```

## Components

### Backend (Python/FastAPI)
- **Purpose**: Central hub for all business logic, scheduling, and data processing.
- **Key Features**:
  - RESTful API for task and schedule management
  - User authentication and authorization
  - Schedule generation using rule-based constraints
  - Machine learning models for personalization
  - Feedback collection and analysis
- **Technologies**: FastAPI, SQLAlchemy, Pydantic, Uvicorn

### Web Client (React/Vite)
- **Purpose**: Browser-based dashboard for schedule viewing and management.
- **Key Features**:
  - Interactive schedule display
  - Task creation and editing
  - User feedback submission
  - Responsive design
- **Technologies**: React, Vite, TypeScript, Recharts (for analytics)

### Desktop Client (Python/PySide6)
- **Purpose**: Native desktop application for users preferring a desktop experience.
- **Key Features**:
  - Schedule viewing and task management
  - System tray integration
  - Offline capabilities (limited)
- **Technologies**: Python, PySide6 (Qt)

### Tauri Desktop App
- **Purpose**: Cross-platform desktop wrapper for the web client.
- **Key Features**:
  - Native window with web content
  - Better performance than Electron
  - Platform-specific integrations
- **Technologies**: Tauri (Rust), React/Vite

### Database
- **Purpose**: Persistent storage for users, tasks, schedules, and feedback.
- **Support**: SQLite (development), MySQL (production)
- **Schema**: Users, Tasks, Schedules, Feedback, Analytics

## Data Flow

1. User creates tasks via any client
2. Backend stores tasks in database
3. Schedule generation runs (rule-based + ML)
4. Clients fetch and display schedules
5. User provides feedback on schedule quality
6. ML models learn from feedback for future optimizations

## Security Considerations

- JWT-based authentication
- Password hashing with bcrypt
- CORS configuration for web clients
- Input validation and sanitization
- 2FA support (TOTP and email)

## Deployment

- Backend: Containerized with Docker or deployed to cloud (Azure, etc.)
- Web: Static hosting (Vercel, Netlify) or served by backend
- Desktop: Platform-specific binaries via Tauri/PyInstaller