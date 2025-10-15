# Quick Start Guide - Enterprise TRA System

## 🚀 Start the Application

```bash
make start
```

This will start both backend and frontend servers.

## 🌐 Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Frontend** | http://localhost:5173/enterprise_tra_home_clean.html | Main application |
| **Backend API** | http://localhost:8000/docs | API documentation |
| **Health Check** | http://localhost:5173/api/health | System status |
| **WebSocket Test** | http://localhost:5173/test_websocket.html | Test WebSocket connection |

## 🛑 Stop the Application

```bash
make stop
```

## 📊 Check Status

```bash
make status
```

## 🔄 Restart

```bash
make restart
```

## 📝 View Logs

```bash
make logs
```

## 🧪 Run Tests

```bash
# Backend tests
make test-backend

# Frontend tests
make test-frontend

# All tests
make test
```

## ⚠️ Important Notes

### First Time Access
When accessing the frontend for the first time or after code changes, **always hard refresh**:
- **Mac:** `Cmd + Shift + R`
- **Windows/Linux:** `Ctrl + Shift + R`

This ensures you get the latest JavaScript files.

### Expected Behavior
✅ **What you SHOULD see:**
- Session ID displayed (e.g., `enterprise_abc123_1234567890`)
- Status: **"Connected"** (green indicator)
- No errors in browser console
- Search functionality works
- Messages can be sent

❌ **What you should NOT see:**
- Status: "Disconnected"
- Import errors in console
- 404 errors for assets
- ReferenceErrors about Alpine.js

### If You See Issues

1. **Hard refresh the browser** (Cmd+Shift+R / Ctrl+Shift+R)
2. **Check server status:**
   ```bash
   make status
   ```
3. **Restart servers if needed:**
   ```bash
   make restart
   ```
4. **Clear browser cache**
5. **Check console for specific errors**

## 📁 Key Files

| File | Purpose |
|------|---------|
| `frontend/vite.config.js` | Vite configuration with proxy settings |
| `frontend/init-store.js` | Alpine.js placeholder store |
| `frontend/enterprise_tra_home_clean.html` | Main HTML file |
| `frontend/assets/js/services/websocket.service.js` | WebSocket connection logic |
| `Makefile` | Server management commands |

## 🔧 Configuration

### Vite Proxy (Development)
- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- API requests: `/api/*` → proxied to backend
- WebSocket: `/ws/*` → proxied to backend

### WebSocket Connection
Development mode automatically uses:
```
ws://localhost:5173/ws/enterprise/{sessionId}
```

This is proxied to:
```
ws://localhost:8000/ws/enterprise/{sessionId}
```

## 📚 Documentation

- [Test Results](TEST_RESULTS.md) - Comprehensive test results
- [Frontend-Backend Connection Fix](docs/frontend/FRONTEND_BACKEND_CONNECTION_FIX.md) - Details of all fixes
- [Makefile Guide](docs/getting-started/MAKEFILE_GUIDE.md) - All available make commands

## 🆘 Troubleshooting

### Problem: "Disconnected" status

**Cause:** Backend not running or WebSocket connection failed

**Solution:**
```bash
make status  # Check if backend is running
make restart # Restart if needed
```

### Problem: Import errors in console

**Cause:** Browser cached old JavaScript files

**Solution:** Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)

### Problem: 404 errors for assets

**Cause:** Asset paths incorrect

**Solution:** All asset paths should use `/css/`, `/js/`, `/images/` (not `assets/...`)

### Problem: Alpine.js ReferenceErrors

**Cause:** `init-store.js` not loading properly

**Solution:**
1. Verify file exists: `http://localhost:5173/init-store.js`
2. Check browser console for loading order
3. Hard refresh browser

## 📞 Support

For issues not covered here, check:
1. Browser console for error messages
2. Backend logs: `make logs`
3. Server status: `make status`
4. Test results: `TEST_RESULTS.md`

---

**Last Updated:** October 15, 2025
**Version:** 2.0.0 - Strands 1.x Native
