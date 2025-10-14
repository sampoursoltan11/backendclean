# Makefile Quick Reference Guide

A comprehensive Makefile has been created to simplify development workflow for the Enterprise TRA project.

---

## 🚀 Quick Start

### First Time Setup
```bash
# Install all dependencies (backend + frontend)
make install
```

### Start Development
```bash
# Start both backend and frontend servers
make start

# Or use the quick start (install + start + open browser)
make quickstart
```

### Stop Servers
```bash
# Stop both servers
make stop
```

---

## 📋 Common Commands

### Development Workflow

| Command | Description |
|---------|-------------|
| `make start` | Start both backend and frontend servers in background |
| `make stop` | Stop both servers |
| `make restart` | Restart both servers |
| `make status` | Show server status (running or not) |
| `make logs` | Show recent logs from both servers |

### Individual Server Control

| Command | Description |
|---------|-------------|
| `make backend` | Start only backend (foreground) |
| `make frontend` | Start only frontend (foreground) |
| `make stop-backend` | Stop only backend |
| `make stop-frontend` | Stop only frontend |
| `make logs-backend` | Tail backend logs (Ctrl+C to exit) |
| `make logs-frontend` | Tail frontend logs (Ctrl+C to exit) |

### Testing

| Command | Description |
|---------|-------------|
| `make test` | Run all tests (backend + frontend) |
| `make test-backend` | Run backend tests only |
| `make test-frontend` | Run frontend tests only |
| `make health` | Check health of running services |

### Build & Deploy

| Command | Description |
|---------|-------------|
| `make build` | Build frontend for production |
| `make preview` | Preview production build |

### Utilities

| Command | Description |
|---------|-------------|
| `make open` | Open application in browser |
| `make open-docs` | Open API documentation |
| `make clean` | Clean logs and temporary files |
| `make clean-all` | Deep clean (including node_modules) |
| `make ps` | Show all related processes |

### Environment

| Command | Description |
|---------|-------------|
| `make env-check` | Check environment and dependencies |
| `make db-status` | Check DynamoDB table status |
| `make s3-status` | Check S3 bucket status |

---

## 📖 Detailed Examples

### Example 1: Start Fresh Development Session
```bash
# Clean previous logs
make clean

# Start both servers
make start

# Check status
make status

# Open in browser
make open
```

**Expected Output:**
```
╔════════════════════════════════════════════════════════════╗
║              Starting Enterprise TRA Servers               ║
╚════════════════════════════════════════════════════════════╝

→ Starting backend server...
  ✓ Backend started (PID: 12345)
→ Starting frontend server...
  ✓ Frontend started (PID: 12346)

Server Status:
  Backend:  ✓ Running (PID: 12345)
  Frontend: ✓ Running (PID: 12346)

✓ Both servers started successfully!

Access the application:
  Frontend: http://localhost:5173/enterprise_tra_home_clean.html
  Backend:  http://localhost:8000/docs

Stop servers with: make stop
```

### Example 2: Check Health Status
```bash
make health
```

**Expected Output:**
```
Health Check:

→ Backend Health:
{
  "status": "running",
  "timestamp": "2025-10-15T01:30:00Z"
}

→ Frontend Server:
  Status: 200
```

### Example 3: View Live Logs
```bash
# Backend logs (real-time)
make logs-backend

# Or frontend logs
make logs-frontend
```

### Example 4: Production Build
```bash
# Build for production
make build

# Preview the build
make preview
```

### Example 5: Complete Environment Check
```bash
make env-check
```

**Expected Output:**
```
Environment Check:

→ Python version:
Python 3.12.5

→ Node version:
v20.10.0

→ NPM version:
10.2.3

→ AWS credentials:
{
    "UserId": "...",
    "Account": "448608816491",
    "Arn": "..."
}

→ DynamoDB table:
"ACTIVE"
```

---

## 🎯 Common Workflows

### Daily Development Workflow
```bash
# Morning: Start servers
make start

# Work on code...
# Servers auto-reload on changes

# Check status if needed
make status

# Evening: Stop servers
make stop
```

### Testing Workflow
```bash
# Start servers
make start

# Run tests
make test

# Check specific component
make test-frontend

# Stop servers
make stop
```

### Debugging Workflow
```bash
# Start servers
make start

# View live logs
make logs-backend  # In one terminal
make logs-frontend # In another terminal

# Check health
make health

# Show processes
make ps
```

### Production Build Workflow
```bash
# Clean previous builds
make clean

# Build production version
make build

# Preview production build
make preview

# Deploy the frontend/dist/ folder
```

---

## 🔧 Troubleshooting

### Problem: Servers won't start
**Solution:**
```bash
# Check if ports are already in use
make ps

# Kill old processes
make stop

# Try starting again
make start
```

### Problem: "Command not found: make"
**Solution:**
```bash
# macOS: Install Xcode Command Line Tools
xcode-select --install

# Linux: Install make
sudo apt-get install make  # Ubuntu/Debian
sudo yum install make      # CentOS/RHEL
```

### Problem: Backend won't connect to AWS
**Solution:**
```bash
# Check AWS credentials
make env-check

# Or check directly
aws sts get-caller-identity

# Configure AWS if needed
aws configure
```

### Problem: Frontend build fails
**Solution:**
```bash
# Reinstall dependencies
make clean-all
make install

# Try building again
make build
```

### Problem: Logs show errors
**Solution:**
```bash
# View recent logs
make logs

# Or view live logs
make logs-backend
make logs-frontend

# Check health status
make health
```

---

## 📁 Log Files

Logs are stored in the `logs/` directory:

- `logs/backend.log` - Backend server logs
- `logs/frontend.log` - Frontend server logs
- `logs/tra_system.log` - Application logs (from backend script)

**View logs:**
```bash
# Recent logs
make logs

# Live tail
make logs-backend

# Or manually
tail -f logs/backend.log
```

---

## 🎨 Color-Coded Output

The Makefile uses color-coded output for better readability:

- 🔵 **Blue** - Headers and section titles
- 🟢 **Green** - Success messages and checkmarks
- 🟡 **Yellow** - Informational messages and prompts
- 🔴 **Red** - Error messages and warnings

---

## 💡 Pro Tips

### 1. Quick Status Check
```bash
# Always know what's running
make status
```

### 2. Clean Start
```bash
# If things are acting weird, clean restart
make stop
make clean
make start
```

### 3. Background Development
```bash
# Start servers in background and continue working
make start

# They'll keep running until you stop them
make stop
```

### 4. Check Before Committing
```bash
# Before committing code
make test
make build
```

### 5. Monitor Both Logs
```bash
# Terminal 1: Backend logs
make logs-backend

# Terminal 2: Frontend logs
make logs-frontend
```

### 6. Health Checks in CI/CD
```bash
# Great for CI/CD pipelines
make start
sleep 5
make health
make test
make stop
```

---

## 🆘 Help

### Get Help
```bash
# Show all available commands
make help

# Or just
make
```

### Command Categories
- **Setup & Installation** - `install`
- **Development** - `start`, `stop`, `restart`, `dev`
- **Control** - `stop-backend`, `stop-frontend`
- **Status & Health** - `status`, `health`, `logs`
- **Testing** - `test`, `test-backend`, `test-frontend`
- **Build** - `build`, `preview`
- **Cleanup** - `clean`, `clean-all`
- **Utilities** - `open`, `ps`, `env-check`

---

## 📚 Additional Resources

- [README.md](README.md) - Project overview
- [TESTING_COMPLETE.md](TESTING_COMPLETE.md) - Testing guide
- [PROJECT_COMPLETION_SUMMARY.md](PROJECT_COMPLETION_SUMMARY.md) - Complete project summary
- [docs/FRONTEND_MANUAL_TESTING.md](docs/FRONTEND_MANUAL_TESTING.md) - Frontend testing guide

---

## ⌨️ Keyboard Shortcuts

While servers are running:

- **Ctrl+C** - Stop a foreground process
- **Ctrl+Z** - Suspend a process (use `bg` to resume in background)

For live logs:
- **Ctrl+C** - Exit tail mode

---

## 🚦 Server Ports

| Service | Port | URL |
|---------|------|-----|
| Frontend (Vite) | 5173 | http://localhost:5173 |
| Backend (FastAPI) | 8000 | http://localhost:8000 |
| API Docs | 8000 | http://localhost:8000/docs |
| WebSocket | 8000 | ws://localhost:8000/ws/enterprise/{sessionId} |

---

## ✅ Quick Reference Card

**Copy this to your terminal:**

```bash
# Setup (first time)
make install

# Start
make start

# Stop
make stop

# Status
make status

# Test
make test

# Help
make help
```

---

**Created:** October 15, 2025
**Version:** 1.0
**Project:** Enterprise TRA System
