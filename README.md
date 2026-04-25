
# Personal Analytics Dashboard

A cross-platform personal analytics and scheduling application that generates daily schedules, adapts to user feedback, and optimizes workload over time using a hybrid rule-based and machine learning approach.

This project includes:
- A web-based dashboard
- A Tauri desktop application
- A Python desktop client (PySide6)
- A shared Python backend for scheduling, analytics, and optimization

---

## Features

- Daily task and schedule generation
- Dynamic schedule updates when tasks or appointments change
- Task prioritization based on importance and deadlines
- User feedback collection (stress / underwhelmed / balanced)
- Adaptive schedule optimization over time
- Web and desktop clients using the same backend logic

---

## System Architecture

The system follows a centralized backend design:

- **Backend (Python / FastAPI)**  
  Handles scheduling logic, task storage, feedback processing, and machine learning.

- **Web Client (React / Vite)**  
  Provides an interactive browser-based dashboard.

- **Tauri Desktop App**  
  Wraps the React frontend in a native desktop window via Tauri (Rust).

- **Python Desktop Client (PySide6)**  
  Alternative desktop application that communicates with the same backend API.

All computation is centralized in the backend to ensure consistency across platforms.

---

## Project Structure

```
personal-analytics-dashboard/
├── backend/          # FastAPI app, scheduler, ML logic, tests
├── web/              # React/Vite frontend + Tauri desktop wrapper
├── desktop/          # Python/PySide6 desktop client
├── launcher/         # Startup scripts (Python + Go)
├── database/         # SQLite database file + schema
├── docs/             # Design and project documentation
│   ├── api-spec.md    # API endpoints and usage
│   ├── architecture.md # System architecture overview
│   ├── ml-design.md   # Machine learning components
│   ├── user-guide.md  # User manual and tutorials
│   └── final-report.pdf # Project final report
├── scripts/          # Utility scripts (e.g., admin seeding)
├── pytest.ini        # Pytest configuration
├── requirements.txt  # Python dependencies
├── SETUP.md          # Detailed setup instructions
├── start-dashboard.bat  # Windows startup script
├── start-dashboard.sh   # Unix startup script
└── TODO.md           # Project milestones and tasks
```

---

## Installation & Setup

Follow these steps to install all required dependencies and run the project locally.

---

## 1. Prerequisites

### Python
- Python **3.10 or newer** is required.
- Download from: https://www.python.org/downloads/

**IMPORTANT (Windows users)**  
During installation, check "Add Python to PATH".

Verify installation:
```bash
python --version
```

### Node.js
- Required to build the React frontend.
- Download from: https://nodejs.org/

Verify installation:
```bash
node --version
npm --version
```

### Rust (for Tauri desktop app)
- Required only if you want to run the Tauri desktop app.
- Download from: https://rustup.rs/

---

## 2. Clone the Repository

```bash
git clone https://github.com/ITSC-4155-Spring-2026-Team-11/personal-analytics-dashboard.git
cd personal-analytics-dashboard
```

---

## Quick Start (All Components Together)

For the fastest setup, use the provided startup scripts:

### Windows
```bat
start-dashboard.bat
```

### macOS / Linux
```bash
./start-dashboard.sh
```

These scripts will:
1. Set up Python virtual environment (if needed)
2. Install/update backend dependencies
3. Build the React frontend (if changes detected)
4. Start the FastAPI backend server
5. Launch the Tauri desktop app (or open web client in browser)

---

## Manual Startup (Component by Component)

### 1. Backend API Server

**Prerequisites**: Python 3.10+, virtual environment

```bash
# Navigate to project root
cd personal-analytics-dashboard

# Create/activate virtual environment
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

**Verification**:
- API: http://127.0.0.1:8000
- Interactive docs: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/health

### Optional: Seed Admin User and Sample Data

For development/testing, you can seed the database with an admin user and sample tasks:

```bash
python scripts/seed_admin.py
```

This creates:
- Admin user: `admin@admin.com` / `Test1234`
- Two weeks of sample tasks (past and future)

Run this after starting the backend for the first time to populate the database with test data.

**Prerequisites**: Node.js 16+, backend running

```bash
# Navigate to web client
cd web/react-version

# Install dependencies (first time only)
npm install

# Start development server
npm run dev
```

**Access**: http://localhost:5173

The web client will connect to the backend at http://127.0.0.1:8000

### 3. Tauri Desktop App

**Prerequisites**: Rust, Node.js, backend running

```bash
# Navigate to web client
cd web/react-version

# Install dependencies (first time only)
npm install

# Start Tauri development app
npm run tauri:dev
```

This opens a native desktop window with the React app inside.

### 4. Python Desktop Client

**Prerequisites**: Python 3.10+, PySide6, backend running

```bash
# Navigate to desktop client
cd desktop

# Install dependencies (if separate venv)
pip install -r requirements.txt

# Run the desktop app
python main.py
```

---

## Running All Components Together (Manual)

1. **Terminal 1 - Backend**:
   ```bash
   cd personal-analytics-dashboard
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   uvicorn backend.app:app --reload
   ```

2. **Terminal 2 - Web Client** (optional):
   ```bash
   cd web/react-version
   npm run dev
   ```

3. **Terminal 3 - Desktop App**:
   ```bash
   cd web/react-version
   npm run tauri:dev
   ```
   Or for Python desktop:
   ```bash
   cd desktop
   python main.py
   ```

---

## Production Deployment

For production:

1. **Backend**: Use a production ASGI server like Gunicorn
2. **Web Client**: Build static files with `npm run build`
3. **Database**: Switch from SQLite to MySQL/PostgreSQL
4. **Security**: Set strong SECRET_KEY, configure CORS properly

See SETUP.md for detailed production configuration.

---

## 7. Common Issues

**uvicorn not found:**
```bash
pip install uvicorn
```

**ModuleNotFoundError:**
1. Make sure the virtual environment is activated
2. Run `pip install -r requirements.txt` from the project root
3. Run uvicorn from the project root (not from inside `backend/`)

**CORS errors in browser:**  
Ensure the backend is running and accessible at `http://127.0.0.1:8000`

---

## Scheduling & ML Plan

This project uses a hybrid approach:

- **Rule-based scheduler** enforces hard constraints and creates a valid schedule.
- **ML components** improve personalization:
  - Supervised model estimates stress from schedule features.
  - Exponential moving average (EMA) adapts scheduling decisions based on user feedback.
